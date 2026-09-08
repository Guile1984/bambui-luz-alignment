"""Consolidação dos resultados do estudo comparativo.

Reúne, em estrutura única, as métricas de cada alternativa e as premissas
que as produziram. Um resultado sem suas premissas é irreprodutível: os
volumes dependem da janela de suavização do greide, e a extensão
inadmissível depende da classe de rodovia adotada.
"""

from dataclasses import dataclass

from bambui_luz.domain.greide import Greide, suavizar
from bambui_luz.domain.perfil import PerfilLongitudinal
from bambui_luz.domain.rodovia import ClasseRodovia
from bambui_luz.domain.terraplenagem import (
    SecaoTransversal,
    VolumesTerraplenagem,
    calcular_volumes,
)
from bambui_luz.services.comparar_alternativas import ResumoAlternativa, resumir


@dataclass(frozen=True, slots=True)
class Premissas:
    """Parâmetros arbitrados que condicionam os resultados do estudo.

    Attributes:
        classe: Classe de rodovia adotada.
        secao: Seção transversal adotada.
        janela_greide_m: Janela de suavização do greide.
        fator_conversao: Volume de aterro compactado por metro cúbico de
            corte no maciço.
        passo_estacao_m: Espaçamento entre estações do perfil.
        resolucao_mde_m: Resolução nominal do modelo de elevação.
    """

    classe: ClasseRodovia
    secao: SecaoTransversal
    janela_greide_m: float
    fator_conversao: float
    passo_estacao_m: float
    resolucao_mde_m: float


@dataclass(frozen=True, slots=True)
class LinhaRelatorio:
    """Resultados consolidados de uma alternativa.

    Attributes:
        resumo: Métricas geométricas e de conformidade.
        volumes: Volumes de terraplenagem.
        rampa_maxima_greide_pct: Maior rampa do greide, em porcentagem.
        segmentos_greide_inadmissiveis: Quantidade de segmentos do greide
            que excedem a classe adotada.
        maior_aterro_m: Maior altura de aterro do traçado.
        maior_corte_m: Maior altura de corte do traçado.
    """

    resumo: ResumoAlternativa
    volumes: VolumesTerraplenagem
    rampa_maxima_greide_pct: float
    segmentos_greide_inadmissiveis: int
    maior_aterro_m: float
    maior_corte_m: float

    @property
    def volume_por_km(self) -> float:
        """Volume movimentado por quilômetro de traçado."""
        return self.volumes.movimentado_m3 / self.resumo.extensao_km


@dataclass(frozen=True, slots=True)
class Relatorio:
    """Relatório consolidado do estudo comparativo.

    Attributes:
        premissas: Parâmetros arbitrados adotados.
        linhas: Resultados de cada alternativa, na ordem de comparação.
    """

    premissas: Premissas
    linhas: tuple[LinhaRelatorio, ...]

    def __post_init__(self) -> None:
        """Valida a estrutura do relatório.

        Raises:
            ValueError: Se não houver alternativa alguma.
        """
        if not self.linhas:
            raise ValueError("o relatório exige ao menos uma alternativa")

    @property
    def referencia(self) -> LinhaRelatorio:
        """Primeira alternativa, adotada como base de comparação."""
        return self.linhas[0]

    def variacao_percentual(self, indice: int, atributo: str) -> float:
        """Calcula a variação de uma métrica em relação à referência.

        Args:
            indice: Posição da alternativa nas linhas do relatório.
            atributo: Nome do atributo a comparar, em `resumo`, `volumes`
                ou na própria linha.

        Returns:
            Variação percentual em relação à referência.

        Raises:
            ValueError: Se o atributo não existir ou se o valor de
                referência for nulo.
        """
        base = _valor(self.referencia, atributo)
        atual = _valor(self.linhas[indice], atributo)
        if base == 0:
            raise ValueError(
                f"a referência tem valor nulo para '{atributo}': "
                "variação percentual indefinida"
            )
        return 100.0 * (atual - base) / base


def _valor(linha: LinhaRelatorio, atributo: str) -> float:
    """Obtém um atributo da linha, do resumo ou dos volumes.

    Args:
        linha: Linha do relatório.
        atributo: Nome do atributo procurado.

    Returns:
        Valor numérico do atributo.

    Raises:
        ValueError: Se o atributo não for encontrado.
    """
    for alvo in (linha, linha.resumo, linha.volumes):
        if hasattr(alvo, atributo):
            return float(getattr(alvo, atributo))
    raise ValueError(f"atributo desconhecido no relatório: '{atributo}'")


def compor_linha(
    nome: str, perfil: PerfilLongitudinal, premissas: Premissas
) -> LinhaRelatorio:
    """Calcula os resultados de uma alternativa a partir de seu perfil.

    Args:
        nome: Identificação da alternativa.
        perfil: Perfil longitudinal do terreno.
        premissas: Parâmetros arbitrados adotados.

    Returns:
        Linha do relatório com métricas e volumes.
    """
    greide: Greide = suavizar(perfil, premissas.janela_greide_m)
    volumes = calcular_volumes(
        perfil, greide, premissas.secao, premissas.fator_conversao
    )
    alturas = [
        estacao_greide.cota_m - estacao_perfil.cota_m
        for estacao_perfil, estacao_greide in zip(
            perfil.estacoes, greide.estacoes, strict=True
        )
    ]
    return LinhaRelatorio(
        resumo=resumir(nome, perfil, premissas.classe),
        volumes=volumes,
        rampa_maxima_greide_pct=greide.rampa_maxima_absoluta,
        segmentos_greide_inadmissiveis=len(
            greide.segmentos_inadmissiveis(premissas.classe)
        ),
        maior_aterro_m=max((a for a in alturas if a > 0), default=0.0),
        maior_corte_m=max((-a for a in alturas if a < 0), default=0.0),
    )
