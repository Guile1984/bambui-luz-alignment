"""Parâmetros e premissas do estudo.

As coordenadas são armazenadas em graus decimais, na forma em que a fonte
as publica. A conversão para o sistema métrico de trabalho é atribuição da
camada de infraestrutura.
"""

from dataclasses import dataclass

CRS_GEOGRAFICO = "EPSG:4674"
"""SIRGAS 2000 geográfico, em graus decimais. Forma de publicação do IBGE."""

CRS_TRABALHO = "EPSG:31983"
"""SIRGAS 2000 / UTM zona 23S, em metros. Sistema de cálculo do estudo."""


@dataclass(frozen=True, slots=True)
class LocalNotavel:
    """Localidade de referência do estudo, como publicada pela fonte.

    Não confundir com Ponto, do domínio: este tipo guarda coordenadas
    geográficas em graus e sua procedência enquanto Ponto opera em metros
    e desconhece a origem do dado.

    Attributes:
        nome: Identificação da localidade.
        latitude_graus: Latitude em graus decimais, negativa ao sul.
        longitude_graus: Longitude em graus decimais, negativa a oeste.
        fonte: Procedência do par de coordenadas. Campo obrigatório.
        altitude_ibge_m: Altitude publicada pela fonte, em metros, quando
            disponível. Usada como aferiação independente do modelo digital
            de elevação, não como dado de cálculo.
    """

    nome: str
    latitude_graus: float
    longitude_graus: float
    fonte: str
    altitude_ibge_m: float | None = None

    def __post_init__(self) -> None:
        """Valida a localidade na construção.

        Raises:
            ValueError: Se o nome ou a fonte estiverem vazios, ou se as
                coordenadas estiverem fora da faixa geográfica válida.
        """
        if not self.nome.strip():
            raise ValueError("a localidade exige um nome não vazio")
        if not self.fonte.strip():
            raise ValueError(
                f"a localidade '{self.nome}' exige a declaração da fonte "
                "das coordenadas"
            )
        if not -90.0 <= self.latitude_graus <= 90.0:
            raise ValueError(
                f"latitude fora da faixa válida em '{self.nome}': {self.latitude_graus}"
            )
        if not -180.0 <= self.longitude_graus <= 180.0:
            raise ValueError(
                f"longitude fora da faixa válida em '{self.nome}': "
                f"{self.longitude_graus}"
            )


FONTE_IBGE = (
    "IBGE, Cadastro de Localidades Selecionadas 2010, "
    "BR_Localidades_2010_v1, consultado em 2026-08-24"
)
"""Procedência das coordenadas das localidades de referência."""

BAMBUI = LocalNotavel(
    nome="Bambuí",
    latitude_graus=-20.011892,
    longitude_graus=-45.979045,
    fonte=FONTE_IBGE,
    altitude_ibge_m=684.938671,
)
"""Sede do município de Bambuí, categoria CIDADE."""

ESTEIOS = LocalNotavel(
    nome="Esteios",
    latitude_graus=-19.928235,
    longitude_graus=-45.704223,
    fonte=FONTE_IBGE,
    altitude_ibge_m=692.065772,
)
"""Sede da vila de Esteios, no município de Luz. Ponto de conexão com a
malha pavimentada existente."""

LUZ = LocalNotavel(
    nome="Luz",
    latitude_graus=-19.796247,
    longitude_graus=-45.683881,
    fonte=FONTE_IBGE,
    altitude_ibge_m=663.733692,
)
"""Sede do município de Luz, categoria CIDADE."""

MARGEM_CORREDOR_M = 5000.0
"""Folga aplicada em torno das localidades ao recortar o modelo de elevação.

Dimensionada para acomodar traçados alternativos que se afastem da linha
reta entre os extremos. Um traçado que alcance a borda do recorte indica
margem insuficiente, não defeito do algoritmo.
"""
