"""Contrato de acesso a dados de elevação.

Declara o que o sistema precisa de uma fonte de elevação, sem determinar
quem a fornece nem como. Permite substituir o modelo digital de elevação
sem alterar as camadas que dependem de cotas.
"""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from bambui_luz.domain.geometria import Ponto


class ElevacaoIndisponivelError(Exception):
    """Erro ao obter a elevação de um ou mais pontos.

    Levantado quando um ponto está fora da cobertura da fonte de elevação
    ou quando a célula correspondente não possui dado válido. A ausência de
    elevação é sinalizada por exceção, e nunca por valor especial, para que
    não se propague silenciosamente pelos cálculos.
    """


@runtime_checkable
class ProvedorElevacao(Protocol):
    """Fonte capaz de informar a elevação de pontos em coordenadas métricas.

    Implementações devem operar no mesmo sistema de referência projetado
    adotado pelo estudo.
    """

    def cotas_em(self, pontos: Sequence[Ponto]) -> tuple[float, ...]:
        """Obtém a elevação de cada ponto informado.

        A consulta é em lote por decisão de contrato: permite que uma
        implementação leia uma única janela do raster em vez de uma
        operação por ponto.

        Args:
            pontos: Pontos em coordenadas métricas projetadas.

        Returns:
            Cotas em metros, na mesma ordem dos pontos recebidos e com o
            mesmo comprimento.

        Raises:
            ElevacaoIndisponivelError: Se algum ponto não tiver elevação
                disponível.
        """
        ...
