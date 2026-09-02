"""Comparação quantitativa entre alternativas de traçado.

As métricas são independentes da função de custo que gerou os traçados:
comparar alternativas pela grandeza que uma delas foi otimizada para
minimizar seria circular.
"""

from dataclasses import dataclass
from itertools import pairwise

from bambui_luz.domain.perfil import PerfilLongitudinal
from bambui_luz.domain.rodovia import ClasseRodovia


@dataclass(frozen=True, slots=True)
class ResumoAlternativa:
    """Métricas de uma alternativa de traçado.

    Attributes:
        nome: Identificação da alternativa.
        extensao_km: Extensão total do traçado.
        subida_acumulada_m: Soma de todos os aclives do perfil.
        descida_acumulada_m: Soma de todos os declives do perfil.
        desnivel_liquido_m: Diferença de cota entre os extremos.
        rampa_maxima_pct: Maior rampa em valor absoluto.
        extensao_inadmissivel_km: Extensão dos segmentos que excedem a
            classe de rodovia adotada.
        estacoes: Quantidade de estações do perfil.
    """

    nome: str
    extensao_km: float
    subida_acumulada_m: float
    descida_acumulada_m: float
    desnivel_liquido_m: float
    rampa_maxima_pct: float
    extensao_inadmissivel_km: float
    estacoes: int

    @property
    def relevo_vencido_m(self) -> float:
        """Soma dos desníveis percorridos, em metros.

        Mede o relevo efetivamente transposto, que o desnível líquido
        oculta: um percurso que sobe e desce muito pode terminar na mesma
        cota em que começou.
        """
        return self.subida_acumulada_m + self.descida_acumulada_m


def resumir(
    nome: str, perfil: PerfilLongitudinal, classe: ClasseRodovia
) -> ResumoAlternativa:
    """Calcula as métricas comparativas de uma alternativa.

    Args:
        nome: Identificação da alternativa.
        perfil: Perfil longitudinal do terreno ao longo do traçado.
        classe: Classe de rodovia cujo limite de rampa será aplicado.

    Returns:
        Resumo com as métricas da alternativa.
    """
    subida = sum(
        b.cota_m - a.cota_m for a, b in pairwise(perfil.estacoes) if b.cota_m > a.cota_m
    )
    descida = sum(
        a.cota_m - b.cota_m for a, b in pairwise(perfil.estacoes) if b.cota_m < a.cota_m
    )
    inadmissiveis = perfil.segmentos_com_rampa_inadmissivel(classe)
    extensao_inadmissivel = sum(
        perfil.estacoes[i + 1].distancia_m - perfil.estacoes[i].distancia_m
        for i in inadmissiveis
    )
    return ResumoAlternativa(
        nome=nome,
        extensao_km=perfil.extensao / 1000,
        subida_acumulada_m=subida,
        descida_acumulada_m=descida,
        desnivel_liquido_m=perfil.desnivel,
        rampa_maxima_pct=perfil.rampa_maxima_absoluta,
        extensao_inadmissivel_km=extensao_inadmissivel / 1000,
        estacoes=len(perfil),
    )
