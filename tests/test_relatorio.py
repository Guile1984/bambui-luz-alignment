"""Testes da consolidação de resultados do estudo."""

import pytest

from bambui_luz.domain.perfil import PerfilLongitudinal, PontoPerfil
from bambui_luz.domain.rodovia import ClasseRodovia
from bambui_luz.domain.terraplenagem import SecaoTransversal
from bambui_luz.services.relatorio import Premissas, Relatorio, compor_linha

PREMISSAS = Premissas(
    classe=ClasseRodovia(
        nome="classe de teste",
        velocidade_diretriz_kmh=60.0,
        rampa_maxima_pct=6.0,
        fonte="valor de exemplo, sem vínculo normativo",
    ),
    secao=SecaoTransversal(
        largura_plataforma_m=10.0,
        talude_corte_h_v=1.0,
        talude_aterro_h_v=1.5,
    ),
    janela_greide_m=300.0,
    fator_conversao=0.9,
    passo_estacao_m=100.0,
    resolucao_mde_m=30.0,
)


def _perfil(cotas: list[float]) -> PerfilLongitudinal:
    return PerfilLongitudinal(
        estacoes=tuple(
            PontoPerfil(distancia_m=indice * 100.0, cota_m=cota)
            for indice, cota in enumerate(cotas)
        )
    )


def test_linha_reune_metricas_e_volumes():
    linha = compor_linha("teste", _perfil([700.0, 710.0, 700.0]), PREMISSAS)
    assert linha.resumo.nome == "teste"
    assert linha.volumes.movimentado_m3 > 0


def test_alturas_extremas_sao_registradas():
    linha = compor_linha("teste", _perfil([700.0, 720.0, 700.0]), PREMISSAS)
    assert linha.maior_corte_m > 0
    assert linha.maior_aterro_m > 0


def test_terreno_plano_nao_gera_movimentacao():
    linha = compor_linha("plano", _perfil([700.0] * 5), PREMISSAS)
    assert linha.volumes.movimentado_m3 == pytest.approx(0.0)
    assert linha.maior_corte_m == 0.0
    assert linha.maior_aterro_m == 0.0


def test_volume_por_km_usa_a_extensao_do_perfil():
    linha = compor_linha("teste", _perfil([700.0, 710.0, 700.0]), PREMISSAS)
    esperado = linha.volumes.movimentado_m3 / linha.resumo.extensao_km
    assert linha.volume_por_km == pytest.approx(esperado)


def test_relatorio_adota_a_primeira_linha_como_referencia():
    linhas = (
        compor_linha("base", _perfil([700.0, 710.0, 700.0]), PREMISSAS),
        compor_linha("outra", _perfil([700.0, 705.0, 700.0]), PREMISSAS),
    )
    relatorio = Relatorio(premissas=PREMISSAS, linhas=linhas)
    assert relatorio.referencia.resumo.nome == "base"


def test_variacao_percentual_compara_com_a_referencia():
    linhas = (
        compor_linha("base", _perfil([700.0, 700.0, 700.0]), PREMISSAS),
        compor_linha("dobro", _perfil([700.0, 700.0, 700.0, 700.0, 700.0]), PREMISSAS),
    )
    relatorio = Relatorio(premissas=PREMISSAS, linhas=linhas)
    assert relatorio.variacao_percentual(1, "extensao_km") == pytest.approx(100.0)


def test_variacao_de_atributo_desconhecido_e_recusada():
    linhas = (compor_linha("base", _perfil([700.0, 710.0]), PREMISSAS),)
    relatorio = Relatorio(premissas=PREMISSAS, linhas=linhas)
    with pytest.raises(ValueError, match="atributo desconhecido"):
        relatorio.variacao_percentual(0, "inexistente")


def test_variacao_sobre_referencia_nula_e_recusada():
    linhas = (
        compor_linha("plano", _perfil([700.0] * 4), PREMISSAS),
        compor_linha("acidentado", _perfil([700.0, 720.0, 700.0, 720.0]), PREMISSAS),
    )
    relatorio = Relatorio(premissas=PREMISSAS, linhas=linhas)
    with pytest.raises(ValueError, match="valor nulo"):
        relatorio.variacao_percentual(1, "movimentado_m3")


def test_relatorio_exige_ao_menos_uma_alternativa():
    with pytest.raises(ValueError, match="ao menos uma"):
        Relatorio(premissas=PREMISSAS, linhas=())
