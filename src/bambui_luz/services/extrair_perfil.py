"""Extração do perfil longitudinal de um traçado.

Orquestra o traçado e uma fonte de elevação para produzir o perfil do
terreno natural, reamostrado em estações regulares.
"""

from bambui_luz.domain.geometria import Tracado
from bambui_luz.domain.perfil import PerfilLongitudinal, PontoPerfil
from bambui_luz.ports.elevacao import ProvedorElevacao

PASSO_ESTACA_M = 100.0
"""Espaçamento padrão entre estações, em metros.

Dimensionado acima da resolução do modelo de elevação (30 m). Passos
menores que a célula produzem rampas artificiais: a 20 m, a rampa máxima
do traçado real chega a 35%, valor que nenhuma via trafegável apresenta.
A estaca convencional de 20 m do projeto rodoviário brasileiro permanece
como unidade de apresentação, não de amostragem.
"""


def extrair_perfil(
    tracado: Tracado,
    provedor: ProvedorElevacao,
    passo_m: float = PASSO_ESTACA_M,
) -> PerfilLongitudinal:
    """Extrai o perfil longitudinal do terreno ao longo de um traçado.

    As estações são espaçadas regularmente, independentemente da posição
    dos vértices do traçdo: vértices concentram-se em curvas e rareiam em
    retas, o que produziria rampas calculadas sobre bases incomparáveis.

    Args:
        tracado: Traçado em coordenadas métricas projetadas.
        provedor: Fonte de elevação.
        passo_m: Espaçamento entre estações, em metros.

    Returns:
        Perfil longitudinal do terreno natural.

    Raises:
        ElevacaoIndisponivelError: Se alguma estação não tiver elevação.
    """
    distancias = tracado.estacoes(passo_m)
    pontos = [tracado.ponto_na_distancia(d) for d in distancias]
    cotas = provedor.cotas_em(pontos)
    return PerfilLongitudinal(
        estacoes=tuple(
            PontoPerfil(distancia_m=distancia, cota_m=cota)
            for distancia, cota in zip(distancias, cotas, strict=True)
        )
    )
