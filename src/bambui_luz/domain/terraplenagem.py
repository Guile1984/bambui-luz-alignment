"""Cálculo de áreas e volumes de terraplenagem.

Adota seção transversal trapezoidal sobre terreno transversalmente
horizontal. A simplificação subestima a área real em encosta, onde o
talude do lado superior é mais alto que o do lado inferior, e por isso os
volumes prestam-se à comparação entre alternativas, não ao dimensionamento.
"""

from dataclasses import dataclass
from itertools import pairwise

from bambui_luz.domain.greide import Greide
from bambui_luz.domain.perfil import PerfilLongitudinal


@dataclass(frozen=True, slots=True)
class SecaoTransversal:
    """Parâmetros geométricos da seção transversal adotada.

    Attributes:
        largura_plataforma_m: Largura da plataforma, em metros.
        talude_corte_h_v: Inclinação do talude de corte, em metros
            horizontais por metro vertical.
        talude_aterro_h_v: Inclinação do talude de aterro, na mesma
            unidade.
    """

    largura_plataforma_m: float
    talude_corte_h_v: float
    talude_aterro_h_v: float

    def __post_init__(self) -> None:
        """Valida os parâmetros da seção na construção.

        Raises:
            ValueError: Se algum parâmetro não for positivo ou se o talude
                de aterro for mais íngreme que o de corte.
        """
        if self.largura_plataforma_m <= 0:
            raise ValueError(
                f"a largura da plataforma deve ser positiva: "
                f"{self.largura_plataforma_m}"
            )
        if self.talude_corte_h_v <= 0 or self.talude_aterro_h_v <= 0:
            raise ValueError(
                f"as inclinações de talude devem ser positivas: "
                f"corte {self.talude_corte_h_v}, aterro {self.talude_aterro_h_v}"
            )
        if self.talude_aterro_h_v < self.talude_corte_h_v:
            raise ValueError(
                "o talude de aterro não pode ser mais íngreme que o de corte: "
                f"aterro {self.talude_aterro_h_v}, corte {self.talude_corte_h_v}"
            )

    def area_corte(self, altura_m: float) -> float:
        """Calcula a área de corte de uma seção.

        Args:
            altura_m: Altura de corte, em metros. Valores não positivos
                resultam em área nula.

        Returns:
            Área da seção, em metros quadrados.
        """
        if altura_m <= 0:
            return 0.0
        return (
            self.largura_plataforma_m * altura_m + self.talude_corte_h_v * altura_m**2
        )

    def area_aterro(self, altura_m: float) -> float:
        """Calcula a área de aterro de uma seção.

        Args:
            altura_m: Altura de aterro, em metros. Valores não positivos
                resultam em área nula.

        Returns:
            Área da seção, em metros quadrados.
        """
        if altura_m <= 0:
            return 0.0
        return (
            self.largura_plataforma_m * altura_m + self.talude_aterro_h_v * altura_m**2
        )


def alturas_de_trabalho(
    perfil: PerfilLongitudinal, greide: Greide
) -> tuple[float, ...]:
    """Calcula a diferença entre greide e terreno em cada estação.

    Args:
        perfil: Perfil do terreno natural.
        greide: Greide de projeto, com as mesmas estações do perfil.

    Returns:
        Alturas em metros. Positivas indicam aterro, negativas indicam
        corte.

    Raises:
        ValueError: Se perfil e greide não tiverem as mesmas estações.
    """
    if len(perfil) != len(greide):
        raise ValueError(
            f"perfil e greide devem ter a mesma quantidade de estações: "
            f"{len(perfil)} e {len(greide)}"
        )
    for estacao_perfil, estacao_greide in zip(
        perfil.estacoes, greide.estacoes, strict=True
    ):
        if estacao_perfil.distancia_m != estacao_greide.distancia_m:
            raise ValueError(
                "perfil e greide devem compartilhar as mesmas distâncias; "
                f"divergência em {estacao_perfil.distancia_m} m"
            )
    return tuple(
        estacao_greide.cota_m - estacao_perfil.cota_m
        for estacao_perfil, estacao_greide in zip(
            perfil.estacoes, greide.estacoes, strict=True
        )
    )


@dataclass(frozen=True, slots=True)
class VolumesTerraplenagem:
    """Volumes de terraplenagem de um traçado.

    Attributes:
        corte_m3: Volume escavado, medido no maciço natural.
        aterro_m3: Volume de aterro necessário, medido compactado.
        fator_conversao: Volume de aterro compactado obtido por metro
            cúbico de corte no maciço.
    """

    corte_m3: float
    aterro_m3: float
    fator_conversao: float

    @property
    def corte_aproveitavel_m3(self) -> float:
        """Volume de aterro compactado obtenível a partir do corte."""
        return self.corte_m3 * self.fator_conversao

    @property
    def saldo_m3(self) -> float:
        """Diferença entre o corte aproveitável e o aterro necessário.

        Positivo indica excesso de material, destinado a bota-fora.
        Negativo indica falta, suprida por jazida de empréstimo.
        """
        return self.corte_aproveitavel_m3 - self.aterro_m3

    @property
    def movimentado_m3(self) -> float:
        """Volume total movimentado, somando escavação e aterro."""
        return self.corte_m3 + self.aterro_m3

    @property
    def compensado(self) -> bool:
        """Informa se o saldo é inferior a 5% do volume movimentado."""
        if self.movimentado_m3 == 0:
            return True
        return abs(self.saldo_m3) / self.movimentado_m3 < 0.05


def volumes_por_segmento(
    perfil: PerfilLongitudinal,
    greide: Greide,
    secao: SecaoTransversal,
) -> tuple[tuple[float, float], ...]:
    """Calcula os volumes de corte e aterro de cada segmento.

    Adota o método das áreas médias. O método do prismoide seria mais
    preciso, mas a diferença é desprezível diante da incerteza do modelo
    de elevação.

    Transições de corte para atero dentro de um segmento não são
    localizadas, o que superestima ligeiramente os volumes nesses pontos.

    Args:
        perfil: Perfil do terreno natural.
        greide: Greide de projeto.
        secao: Parâmetros geométricos da seção transversal.

    Returns:
        Pares de volume de corte e aterro, em metros cúbicos, um por
        segmento entre estações consecutivas.
    """
    alturas = alturas_de_trabalho(perfil, greide)
    areas_corte = [secao.area_corte(-altura) for altura in alturas]
    areas_aterro = [secao.area_aterro(altura) for altura in alturas]

    resultado = []
    for indice, (anterior, atual) in enumerate(pairwise(perfil.estacoes)):
        distancia = atual.distancia_m - anterior.distancia_m
        corte = (areas_corte[indice] + areas_corte[indice + 1]) / 2 * distancia
        aterro = (areas_aterro[indice] + areas_aterro[indice + 1]) / 2 * distancia
        resultado.append((corte, aterro))
    return tuple(resultado)


def calcular_volumes(
    perfil: PerfilLongitudinal,
    greide: Greide,
    secao: SecaoTransversal,
    fator_conversao: float,
) -> VolumesTerraplenagem:
    """Totaliza os volumes de terraplenagem de um traçado.

    Args:
        perfil: Perfil do terreno natural.
        greide: Greide de projeto.
        secao: Parâmetros geométricos da seção transversal.
        fator_conversao: Volume de aterro compactado por metro cúbico de
            corte no maciço.

    Returns:
        Volumes totais de corte e aterro.

    Raises:
        ValueError: Se o fator de conversão não estiver entre 0 e 1.
    """
    if not 0 < fator_conversao <= 1:
        raise ValueError(
            f"o fator de conversão deve estar entre 0 e 1: {fator_conversao}"
        )
    segmentos = volumes_por_segmento(perfil, greide, secao)
    return VolumesTerraplenagem(
        corte_m3=sum(corte for corte, _ in segmentos),
        aterro_m3=sum(aterro for _, aterro in segmentos),
        fator_conversao=fator_conversao,
    )


def curva_de_massa(
    perfil: PerfilLongitudinal,
    greide: Greide,
    secao: SecaoTransversal,
    fator_conversao: float,
) -> tuple[float, ...]:
    """Calcula as ordenadas da curva de massa ao longo do traçado.

    A curva acumula o saldo entre o corte aproveitável e o aterro
    necessário. Trechos ascendentes indicam excesso de material; trechos
    descendentes, falta. A ordenada final revela se o traçado é compensado.

    Args:
        perfil: Perfil do terreno natural.
        greide: Greide de projeto.
        secao: Parâmetros geométricos da seção transversal.
        fator_conversao: Volume de aterro compactado por metro cúbico de
            corte no maciço.

    Returns:
        Ordenadas em metros cúbicos, começando em 0.0 e com um valor por
        estação do perfil.
    """
    ordenadas = [0.0]
    for corte, aterro in volumes_por_segmento(perfil, greide, secao):
        ordenadas.append(ordenadas[-1] + corte * fator_conversao - aterro)
    return tuple(ordenadas)
