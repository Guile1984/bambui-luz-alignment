"""Perfil longitudinal do terreno e verificação de rampas.

O perfil modelado aqui é o do terreno natural ao longo de um traçado. O
limite normativo de rampa aplica-se ao greide, não ao terreno: um trecho
com declividade natural acima do limite não é inviável, e sim indicativo
de que haverá movimentação de terra naquele segmento.
"""

from dataclasses import dataclass
from itertools import pairwise
from math import isfinite

from bambui_luz.domain.rodovia import ClasseRodovia

TOLERANCIA_DISTANCIA_M = 1e-6
"""Avanço mínimo, em metros, entre estações consecutivas do perfil."""


@dataclass(frozen=True, slots=True)
class PontoPerfil:
    """Estação do perfil longitudinal.

    Attributes:
        distancia_m: Distância horizontal acumulada desde a origem do
            traçado, em metros.
        cota_m: Cota do terreno natural na estação, em metros.
    """

    distancia_m: float
    cota_m: float

    def __post_init__(self) -> None:
        """Valida a estação na construção.

        Raises:
            ValueError: Se os valores não forem finitos ou se a distância
                for negativa.
        """
        if not isfinite(self.distancia_m) or not isfinite(self.cota_m):
            raise ValueError(
                f"distância e cota deve ser finitas: "
                f"distancia_m={self.distancia_m}, cota_m={self.cota_m}"
            )
        if self.distancia_m < 0:
            raise ValueError(
                f"a distância acumulada não pode ser negativa: {self.distancia_m}"
            )


@dataclass(frozen=True, slots=True)
class PerfilLongitudinal:
    """Sequência de estações que descreve o terreno ao longo de um traçado.

    Attributes:
        estacoes: Estações em ordem estritamente crescente de distância.
            Exige ao menos duas estações.
    """

    estacoes: tuple[PontoPerfil, ...]

    def __post_init__(self) -> None:
        """Valida a estrutura do perfil na construção.

        Raises:
            TypeError: Se as estações não forem fornecidas em uma tupla.
            ValueError: Se houver menos de duas estações ou se as
                distâncias não forem estritamente crescentes.
        """
        if not isinstance(self.estacoes, tuple):
            raise TypeError(
                "as estaões devem ser uma tupla, para garantir imutabilidade; "
                f"recebido: {type(self.estacoes).__name__}"
            )
        if len(self.estacoes) < 2:
            raise ValueError(
                f"um perfil exige ao menos duas estações; "
                f"recebidas: {len(self.estacoes)}"
            )
        for indice, (anteior, atual) in enumerate(pairwise(self.estacoes)):
            avanco = atual.distancia_m - anteior.distancia_m
            if avanco < TOLERANCIA_DISTANCIA_M:
                raise ValueError(
                    f"as distâncias devem ser estritamente crescentes; "
                    f"avanço inválido entre as estações {indice} e "
                    f"{indice + 1}: {avanco} m"
                )

    def __len__(self) -> int:
        """Retorna a quantidade de estações do perfil."""
        return len(self.estacoes)

    @property
    def extensao(self) -> float:
        """Extensão horizontal coberta pelo perfil, em metros."""
        return self.estacoes[-1].distancia_m - self.estacoes[0].distancia_m

    @property
    def desnivel(self) -> float:
        """Diferença de cota entre a última e a primeira estação, em metros."""
        return self.estacoes[-1].cota_m - self.estacoes[0].cota_m

    def rampas(self) -> tuple[float, ...]:
        """Calula a rampa de cada segmento entre estações consecutivas.

        Returns:
            Rampas em porcentagem, positivas em aclive e negativas em
            declive, no sentido de percurso do perfil. Tem um elemento a
            menos que a quantidade de estações.
        """
        return tuple(
            (atual.cota_m - anterior.cota_m)
            / (atual.distancia_m - anterior.distancia_m)
            * 100
            for anterior, atual in pairwise(self.estacoes)
        )

    @property
    def rampa_maxima_absoluta(self) -> float:
        """Maior rampa do perfil em valor absoluto, em porcentagem."""
        return max(abs(rampa) for rampa in self.rampas())

    def segmentos_com_rampa_inadmissivel(
        self, classe: ClasseRodovia
    ) -> tuple[int, ...]:
        """Localiza os segmentos cuja declividade natural excede a classe.

        O resultado não indica inviabilidade: aponta os segmentos em que o
        greide não poderá acompanhar o terreno e, portanto, haverá
        movimentação de terra.

        Args:
            classe: Classe de rodovia cujo limite de rampa será aplicado.

        Returns:
            Índices dos segmentos que excedem o limite, em ordem crescente.
            O segmento do indice i liga a estação i à estação i + 1.
        """
        return tuple(
            indice
            for indice, rampa in enumerate(self.rampas())
            if not classe.rampa_admissivel(rampa)
        )
