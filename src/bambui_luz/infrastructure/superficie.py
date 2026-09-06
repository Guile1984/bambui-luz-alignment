"""Cálculo de superfícies derivadas do modelo digital de elevação.

Opera sobre grades em coordenadas geográficas, cujas células não são
quadradas em metros: um segundo de longitude é mais curto que um de
latitude. As dimensões reais são calculadas e aplicadas separadamente em
cada direção, evitando a reprojeção do raster.
"""

import numpy as np
from pyproj import Geod

ELIPSOIDE = "GRS80"
"""Elipsoide de referência do SIRGAS 2000 e do WGS 84."""


def dimensoes_celula_m(
    largura_graus: float, altura_graus: float, latitude_graus: float
) -> tuple[float, float]:
    """Calcula as dimensões de uma célula geográfica em metros.

    A dimensão horizontal depende da latitude; a vertica é praticamente
    constante. Adota-se a latitude informada como representativa, o que
    introduz erro inferior a 0,5% em corredores de poucos décimos de grau.

    Args:
        largura_graus: Extensão da célula em longitude, em graus.
        altura_graus: Extensão da célula em latitude, em graus.
        latitude_graus: Latitude representativa da área de estudo.

    Returns:
        Largura e altura da célula, em metros.
    """
    geodesico = Geod(ellps=ELIPSOIDE)
    _, _, largura_m = geodesico.inv(0.0, latitude_graus, largura_graus, latitude_graus)
    _, _, altura_m = geodesico.inv(
        0.0, latitude_graus, 0.0, latitude_graus + altura_graus
    )
    return largura_m, altura_m


def calcular_declividade(
    cotas: np.ndarray,
    largura_celula_m: float,
    altura_celula_m: float,
    cota_ausente: float = 0.0,
) -> np.ndarray:
    """Calcula a declividade máxima de cada célula, em porcentagem.

    Células sem dado válido e suas vizinhas resultam em NaN: a derivada
    junto a uma lacuna é indeterminada, e propagá-la é preferível a
    produzir um valor plausível e falso.

    Args:
        cotas: Grade de elevações, em metros.
        largura_celula_m: Dimensão da célula na direção leste-oeste.
        altura_celula_m: Dimensão da célula na direção norte-sul.
        cota_ausente: Valor que representa célual sem dado válido.

    Returns:
        Grade de declividade em porcentagem, com NaN onde indeterminada.

    Raises:
        ValueError: Se alguma dimensão de célula não for positiva.
    """
    if largura_celula_m <= 0 or altura_celula_m <= 0:
        raise ValueError(
            f"as dimensões da célula devem ser positivas: "
            f"{largura_celula_m} x {altura_celula_m}"
        )
    validas = np.where(cotas == cota_ausente, np.nan, cotas.astype("float64"))
    variacao_norte_sul, variacao_leste_oeste = np.gradient(validas)
    declividade = (
        np.hypot(
            variacao_leste_oeste / largura_celula_m,
            variacao_norte_sul / altura_celula_m,
        )
        * 100.0
    )
    return np.where(np.isnan(validas), np.nan, declividade)


def compor_custo(
    declividade_pct: np.ndarray,
    declividade_referencia_pct: float,
    peso_declividade: float,
    declividade_barreira_pct: float,
    custo_barreira: float,
    posicao_topografica_m: np.ndarray | None = None,
    posicao_referencia_m: float = 10.0,
    peso_talvegue: float = 0.0,
) -> np.ndarray:
    """Compõe a superfície de custo de atravessamento.

    O custo cresce com o quadrado da declividade normalizada: o volume de
    terraplenagem cresce mais rápido que a inclinação.

    Quando informada a posição topográfica, acrescenta-se penalidade
    quadrática apenas às células rebaixadas em relação ao entorno. A
    assimetria é deliberada: permite o traçado por divisores de água e
    desencoraja o fundo de vale, cujo custo real de drenagem, risco de
    inundação e restrição ambiental não é representado pela declividade.

    Células sem dado recebem custo de barreira.

    Args:
        declividade_pct: Grade de declividades em porcentagem.
        declividade_referencia_pct: Declividade que normaliza a penalidade.
        peso_declividade: Custo adicional de atravessar uma encosta com a
            declividade de referência, em múltiplos do custo base.
        declividade_barreira_pct: Limite acima do qual a travessia é
            desencorajada.
        custo_barreira: Custo atribuído acima do limite.
        posicao_topografica_m: Grade do índice de posição topográfica.
            Quando None, a penalidade de talvegue não é aplicada.
        posicao_referencia_m: Rebaixamento que normaliza a penalidade de
            talvegue.
        peso_talvegue: Custo adicional de atravessar célula rebaixada em
            relação ao entorno na medida de referência.

    Returns:
        Grade de custos, sempre positiva e sem valores indeterminados.

    Raises:
        ValueError: Se algum parâmetro estiver fora de faixa válida.
    """
    if declividade_referencia_pct <= 0:
        raise ValueError(
            f"a declividade de referência deve ser positiva: "
            f"{declividade_referencia_pct}"
        )
    if peso_declividade < 0:
        raise ValueError(
            f"o peso da declividade não pode ser negativo: {peso_declividade}"
        )
    if custo_barreira <= 1.0:
        raise ValueError(
            f"o custo de barreira deve superar o custo base: {custo_barreira}"
        )
    if posicao_referencia_m <= 0:
        raise ValueError(
            f"a posição de referência deve ser positiva: {posicao_referencia_m}"
        )
    if peso_talvegue < 0:
        raise ValueError(f"o peso de talvegue não pode ser negativo: {peso_talvegue}")

    normalizada = declividade_pct / declividade_referencia_pct
    custo = 1.0 + peso_declividade * np.square(normalizada)

    indeterminada = np.isnan(declividade_pct)
    if posicao_topografica_m is not None and peso_talvegue > 0:
        rebaixamento = np.maximum(0.0, -posicao_topografica_m)
        custo = custo + peso_talvegue * np.square(rebaixamento / posicao_referencia_m)
        indeterminada = indeterminada | np.isnan(posicao_topografica_m)

    custo = np.where(declividade_pct > declividade_barreira_pct, custo_barreira, custo)
    return np.where(indeterminada, custo_barreira, custo)


def calcular_posicao_topografica(
    cotas: np.ndarray,
    raio_celulas: int,
    cota_ausente: float = 0.0,
) -> np.ndarray:
    """Calcula o índice de posição topográfica de cada célula.

    O índice é a diferença entre a cota da célula e a média das cotas de
    sua vizinhança. Valores positivos indicam posição elevada em relação
    ao entorno, como divisores de água; negativa indicam posição rebaixada,
    como talvegues.

    Distingue formas de relevo que a declividade não separa: o topo de um
    divisor e o fundo de um vale podem ter a mesma declividade e posições
    topográficas opostas.

    Args:
        cotas: Grade de elevações, em metros.
        raio_celulas: Raio da vizinhança, em células.
        cota_ausente: Valor que representa célula sem dado válido.

    Returns:
        Grade de índices em metros, com NaN onde indeterminado.

    Raises:
        ValueError: Se o raio não for positivo.
    """
    if raio_celulas <= 0:
        raise ValueError(f"o raio da vizinhança deve ser positivo: {raio_celulas}")
    validas = np.where(cotas == cota_ausente, np.nan, cotas.astype("float64"))
    lado = 2 * raio_celulas + 1
    acumulado = np.zeros_like(validas)
    contagem = np.zeros_like(validas)

    for deslocamento_linha in range(-raio_celulas, raio_celulas + 1):
        for deslocamento_coluna in range(-raio_celulas, raio_celulas + 1):
            deslocada = np.roll(
                validas, (deslocamento_linha, deslocamento_coluna), axis=(0, 1)
            )
            presentes = ~np.isnan(deslocada)
            acumulado += np.where(presentes, deslocada, 0.0)
            contagem += presentes

    media = np.divide(
        acumulado, contagem, out=np.full_like(acumulado, np.nan), where=contagem > 0
    )
    del lado
    return np.where(np.isnan(validas), np.nan, validas - media)
