"""Testes das entidades geométricas do domínio."""

from dataclasses import FrozenInstanceError

import pytest

from bambui_luz.domain.geometria import Ponto, Tracado


def test_ponto_armazena_coordenadas_metricas():
    ponto = Ponto(x=397802.68, y=7787224.59)
    assert ponto.x == pytest.approx(397802.68)
    assert ponto.y == pytest.approx(7787224.59)


def test_ponto_aceita_cota_opcional():
    ponto = Ponto(x=100.0, y=200.0, cota=661.0)
    assert ponto.cota == pytest.approx(661.0)


def test_ponto_e_imutavel():
    ponto = Ponto(x=0.0, y=0.0)
    with pytest.raises(FrozenInstanceError):
        ponto.x = 10.0


def test_ponto_rejeita_coordenada_nao_finita():
    with pytest.raises(ValueError, match="finitas"):
        Ponto(x=float("inf"), y=0.0)


def test_ponto_rejeita_cota_nao_finita():
    with pytest.raises(ValueError, match="cota"):
        Ponto(x=0.0, y=0.0, cota=float("nan"))


def test_distancia_horizontal_entre_pontos():
    origem = Ponto(x=0.0, y=0.0)
    destino = Ponto(x=3.0, y=4.0)
    assert origem.distancia_ate(destino) == pytest.approx(5.0)


def test_distancia_ignora_a_cota():
    origem = Ponto(x=0.0, y=0.0, cota=0.0)
    destino = Ponto(x=3.0, y=4.0, cota=1000.0)
    assert origem.distancia_ate(destino) == pytest.approx(5.0)


def _tracado_simples() -> Tracado:
    return Tracado(
        pontos=(
            Ponto(x=0.0, y=0.0),
            Ponto(x=300.0, y=400.0),
            Ponto(x=300.0, y=1400.0),
        )
    )


def test_tracado_calcula_extensao():
    assert _tracado_simples().extensao == pytest.approx(1500.0)


def test_tracado_reporta_quantidade_de_pontos():
    assert len(_tracado_simples()) == 3


def test_distancias_acumuladas_comecam_na_origem():
    acumuladas = _tracado_simples().distancias_acumuladas()
    assert acumuladas == pytest.approx((0.0, 500.0, 1500.0))


def test_tracado_exige_tupla_e_nao_lista():
    with pytest.raises(TypeError, match="tupla"):
        Tracado(pontos=[Ponto(x=0.0, y=0.0), Ponto(x=1.0, y=1.0)])


def test_tracado_rejeita_ponto_unico():
    with pytest.raises(ValueError, match="dois pontos"):
        Tracado(pontos=(Ponto(x=0.0, y=0.0),))


def test_tracado_rejeita_pontos_consecutivos_coincidentes():
    with pytest.raises(ValueError, match="coincidentes"):
        Tracado(
            pontos=(
                Ponto(x=0.0, y=0.0),
                Ponto(x=0.0, y=0.0),
                Ponto(x=100.0, y=0.0),
            )
        )
