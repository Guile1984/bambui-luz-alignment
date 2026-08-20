"""Entidades geométricas fundamentais do domínio.

Todas as coordenadas são expressas em metros, em sistema de referência
projetado. O domínio não converte coordenadas nem conhece sistemas de
referência: essa responsabilidade pertence à camada de infraestrutura.
"""

from dataclasses import dataclass
from itertools import pairwise
from math import hypot, isfinite


@dataclass(frozen=True, slots=True)
class Ponto:
    """Ponto no plano, em coordenadas métricas projetadas.

    Attribuites:
        x: Coordenada Este, em metros.
        y: Coordenada Norte, em metros.
        cota: Altitude em metros, quando conhecida. None indica que a
            elevação ainda não foi determinada para este ponto.
    """

    x: float
    y: float
    cota: float | None = None

    def __post_init__(self) -> None:
        """Valida as coordenadas na construção do objeto.

        Raises:
            ValueError: Se alguma coordenada não for um número finito.
        """
        if not isfinite(self.x) or not isfinite(self.y):
            raise ValueError(
                f"as coordenadas devem ser finitas: x={self.x}, y={self.y}"
            )
        if self.cota is not None and not isfinite(self.cota):
            raise ValueError(f"a cota deve ser finita quando informada: {self.cota}")

    def distancia_ate(self, outro: "Ponto") -> float:
        """Calcula a distância horizontal até outro ponto.

        A cota é ignorada: trata-se da distância em projeção horizontal,
        que é a base do estanqueamento em projeto rodoviário.

        Args:
            outro: Ponto de destino.

        Returns:
            Distância em metros.
        """
        return hypot(outro.x - self.x, outro.y - self.y)


TOLERANCIA_COINCIDENCIA_M = 1e-6
"""Distância mínima, em metros, para dois pontos serem considerados distintos."""


@dataclass(frozen=True, slots=True)
class Tracado:
    """Sequência ordenada de pontos que define um eixo em planta.

    Attributes:
        pontos: Pontos do traçado, na ordem de percurso. Deve ser uma tupla
            com ao menos dois pontos distintos entre si.
    """

    pontos: tuple[Ponto, ...]

    def __post_init__(self) -> None:
        """Valida a estrutura do traçado na construção.

        Raises:
            TypeError: Se os pontos não forem fornecidos em uma tupla.
            ValueError: Se houver menos de dois pontos ou se dois pontos
                consecutivos forem coincidentes.
        """
        if not isinstance(self.pontos, tuple):
            raise TypeError(
                "os pontos devem ser um tupla, para garantir imutabilidade; "
                f"recebido: {type(self.pontos).__name__}"
            )
        if len(self.pontos) < 2:
            raise ValueError(
                f"um traçado exige ao menos dois pontos; recebidos: {len(self.pontos)}"
            )
        for indice, (anterior, atual) in enumerate(pairwise(self.pontos)):
            if anterior.distancia_ate(atual) < TOLERANCIA_COINCIDENCIA_M:
                raise ValueError(
                    f"pontos consecutivos coincidentes nas posições "
                    f"{indice} e {indice + 1}"
                )

    def __len__(self) -> int:
        """Retorna a quantidade de pontos do traçado."""
        return len(self.pontos)

    @property
    def extensao(self) -> float:
        """Extensão horizontal total do traçado, em metros."""
        return sum(
            anterior.distancia_ate(atual) for anterior, atual in pairwise(self.pontos)
        )

    def distancias_acumuladas(self) -> tuple[float, ...]:
        """Calcula a distância percorrida desde a origem até cada ponto.

        Returns:
            Distâncias em metros, começando em 0.0 para o primeiro ponto.
            Tem o mesmo comprimento que os pontos do traçado.
        """
        acumuladas = [0.0]
        for anterior, atual in pairwise(self.pontos):
            acumuladas.append(acumuladas[-1] + anterior.distancia_ate(atual))
        return tuple(acumuladas)
