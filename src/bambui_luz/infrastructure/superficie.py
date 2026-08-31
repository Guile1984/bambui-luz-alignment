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
) -> np.ndarray:
    """Compõe a superfície de custo de atravessamento a partir a declividade.

    O custo cresce com o quadrado da declividade normalizada: o volume de
    terraplenagem cresce mais rápido que a inclinação, de modo que uma
    encosta com o dobro da declividade custa mais que o dobro.

    Células sem declividade definida recebem custo de barreira: sem dado de
    elevação, a travessia não pode ser avaliada.

    Args:
        declividade_pct: Grade de declividades em porcentagem.
        declividade_referencia_pct: Declividade que normaliza a penalidade.
        peso_declividade: Custo adicional de atravessar uma encosta com a
            declividade de referência, em múltiplos do custo base.
        declividade_barreira_pct: Limite acima do qual a travessia é
            desencorajada.
        custo_barreira: Custo atribuído acima do limite.

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

    normaliza = declividade_pct / declividade_referencia_pct
    custo = 1.0 + peso_declividade * np.square(normaliza)
    custo = np.where(declividade_pct > declividade_barreira_pct, custo_barreira, custo)
    return np.where(np.isnan(declividade_pct), custo_barreira, custo)
