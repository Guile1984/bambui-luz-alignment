"""Testes da comparação entre alternativas de traçado."""

import pytest

from bambui_luz.domain.perfil import PerfilLongitudinal, PontoPerfil
from bambui_luz.domain.rodovia import ClasseRodovia
from bambui_luz.services.comparar_alternativas import resumir

CLASSE = ClasseRodovia(
    nome="classe de teste",
    velocidade_diretriz_kmh=80.0,
    rampa_maxima_pct=6.0,
    fonte="valor de exemplo, sem vínculo normativo",
)


def _perfil_serrilhado() -> PerfilLongitudinal:
    """Sobe 10 m, desce 10 m, sobe 10 m, a cada 100 m."""
    return PerfilLongitudinal(
        estacoes=(
            PontoPerfil(distancia_m=0.0, cota_m=700.0),
            PontoPerfil(distancia_m=100.0, cota_m=710.0),
            PontoPerfil(distancia_m=200.0, cota_m=700.0),
            PontoPerfil(distancia_m=300.0, cota_m=710.0),
        )
    )


def test_relevo_vencido_supera_o_desnivel_liquido():
    resumo = resumir("serrilhado", _perfil_serrilhado(), CLASSE)
    assert resumo.desnivel_liquido_m == pytest.approx(10.0)
    assert resumo.subida_acumulada_m == pytest.approx(20.0)
    assert resumo.descida_acumulada_m == pytest.approx(10.0)
    assert resumo.relevo_vencido_m == pytest.approx(30.0)


def test_extensao_em_quilometros():
    assert resumir("t", _perfil_serrilhado(), CLASSE).extensao_km == pytest.approx(0.3)


def test_rampa_maxima_absoluta():
    assert resumir("t", _perfil_serrilhado(), CLASSE).rampa_maxima_pct == pytest.approx(
        10.0
    )


def test_todos_os_segmentos_excedem_a_classe():
    """Rampa de 10% conta limite de 6%: os trÊs segmentos violam."""
    resumo = resumir("t", _perfil_serrilhado(), CLASSE)
    assert resumo.extensao_inadmissivel_km == pytest.approx(0.3)


def test_pefil_suave_nao_tem_extensao_inadmissivel():
    perfil = PerfilLongitudinal(
        estacoes=(
            PontoPerfil(distancia_m=0.0, cota_m=700.0),
            PontoPerfil(distancia_m=100.0, cota_m=702.0),
        )
    )
    assert resumir("suave", perfil, CLASSE).extensao_inadmissivel_km == 0.0


def test_quantidade_de_estacoes_e_registrada():
    assert resumir("t", _perfil_serrilhado(), CLASSE).estacoes == 4
