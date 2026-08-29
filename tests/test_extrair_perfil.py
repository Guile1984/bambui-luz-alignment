"""Testes da extração de perfil longitudinal."""

from collections.abc import Sequence

import pytest

from bambui_luz.domain.geometria import Ponto, Tracado
from bambui_luz.services.extrair_perfil import extrair_perfil


class ProvedorPlanoInclinado:
    """Cota cresce 5 m a cada 100 m de Este, a partir de 700 m."""

    def cotas_em(self, pontos: Sequence[Ponto]) -> tuple[float, ...]:
        return tuple(700.0 + ponto.x * 0.05 for ponto in pontos)


def _tracado_reto() -> Tracado:
    return Tracado(pontos=(Ponto(x=0.0, y=0.0), Ponto(x=1000.0, y=0.0)))


def test_perfil_reamostra_em_estacoes_regulares():
    perfil = extrair_perfil(_tracado_reto(), ProvedorPlanoInclinado(), passo_m=100.0)
    distancias = [e.distancia_m for e in perfil.estacoes]
    assert distancias == pytest.approx([float(d) for d in range(0, 1001, 100)])


def test_perfil_sobre_plano_inclinado_tem_rampa_constante():
    perfil = extrair_perfil(_tracado_reto(), ProvedorPlanoInclinado(), passo_m=100.0)
    assert perfil.rampas() == pytest.approx([5.0] * 10)


def test_extensao_do_perfil_confere_com_a_do_tracado():
    tracado = _tracado_reto()
    perfil = extrair_perfil(tracado, ProvedorPlanoInclinado(), passo_m=100.0)
    assert perfil.extensao == pytest.approx(tracado.extensao)


def test_ultima_estacao_alcanca_o_fim_mesmo_com_passo_irregular():
    perfil = extrair_perfil(_tracado_reto(), ProvedorPlanoInclinado(), passo_m=300.0)
    assert perfil.estacoes[-1].distancia_m == pytest.approx(1000.0)


def test_ponto_na_distancia_interpola_entre_vertices():
    tracado = Tracado(
        pontos=(Ponto(x=0.0, y=0.0), Ponto(x=100.0, y=0.0), Ponto(x=100.0, y=100.0))
    )
    meio = tracado.ponto_na_distancia(150.0)
    assert meio.x == pytest.approx(100.0)
    assert meio.y == pytest.approx(50.0)


def test_ponto_na_distancia_recusa_valor_fora_do_tracado():
    with pytest.raises(ValueError, match="fora do traçado"):
        _tracado_reto().ponto_na_distancia(2000.0)


def test_estacoes_recusam_passo_nao_positivo():
    with pytest.raises(ValueError, match="positivo"):
        _tracado_reto().estacoes(0.0)
