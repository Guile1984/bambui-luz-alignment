"""Testes do perfil longitudinal e da verificação de rampas."""

import pytest

from bambui_luz.domain.perfil import PerfilLongitudinal, PontoPerfil
from bambui_luz.domain.rodovia import ClasseRodovia


def _perfil() -> PerfilLongitudinal:
    """Perfil com aclive de 5% seguido de declive de 10%."""
    return PerfilLongitudinal(
        estacoes=(
            PontoPerfil(distancia_m=0.0, cota_m=700.0),
            PontoPerfil(distancia_m=100.0, cota_m=705.0),
            PontoPerfil(distancia_m=200.0, cota_m=695.0),
        )
    )


def _classe(rampa_maxima_pct: float) -> ClasseRodovia:
    return ClasseRodovia(
        nome="classe de teste",
        velocidade_diretriz_kmh=80.0,
        rampa_maxima_pct=rampa_maxima_pct,
        fonte="Valor de exemplo, sem vínculo normativo",
    )


def test_rampas_de_cada_segmento():
    assert _perfil().rampas() == pytest.approx((5.0, -10.0))


def test_extensao_e_desnivel_do_perfil():
    perfil = _perfil()
    assert perfil.extensao == pytest.approx(200.0)
    assert perfil.desnivel == pytest.approx(-5.0)


def test_rampa_maxima_usa_valor_absoluto():
    assert _perfil().rampa_maxima_absoluta == pytest.approx(10.0)


def test_perfil_reporta_quantidade_de_estacoes():
    assert len(_perfil()) == 3


def test_segmento_em_declive_acentuado_e_apontado():
    assert _perfil().segmentos_com_rampa_inadmissivel(_classe(6.0)) == (1,)


def test_perfil_sem_segmento_inadmissivel_retorna_vazio():
    assert _perfil().segmentos_com_rampa_inadmissivel(_classe(12.0)) == ()


def test_todos_os_segmentos_podem_ser_apontados():
    assert _perfil().segmentos_com_rampa_inadmissivel(_classe(3.0)) == (0, 1)


def test_perfil_exige_tupla():
    with pytest.raises(TypeError, match="tupla"):
        PerfilLongitudinal(
            estacoes=[
                PontoPerfil(distancia_m=0.0, cota_m=700.0),
                PontoPerfil(distancia_m=100.0, cota_m=705.0),
            ]
        )


def test_perfil_rejeita_estacao_unica():
    with pytest.raises(ValueError, match="duas estações"):
        PerfilLongitudinal(estacoes=(PontoPerfil(distancia_m=0.0, cota_m=700.0),))


def test_perfil_rejeita_distancias_nao_crescentes():
    with pytest.raises(ValueError, match="crescentes"):
        PerfilLongitudinal(
            estacoes=(
                PontoPerfil(distancia_m=0.0, cota_m=700.0),
                PontoPerfil(distancia_m=100.0, cota_m=705.0),
                PontoPerfil(distancia_m=100.0, cota_m=710.0),
            )
        )


def test_ponto_perfil_rejeita_distancia_negativa():
    with pytest.raises(ValueError, match="negativa"):
        PontoPerfil(distancia_m=-1.0, cota_m=700.0)
