"""Testes do cálculo de áreas de terraplenagem."""

import pytest

from bambui_luz.domain.greide import Greide
from bambui_luz.domain.perfil import PerfilLongitudinal, PontoPerfil
from bambui_luz.domain.terraplenagem import (
    SecaoTransversal,
    alturas_de_trabalho,
    calcular_volumes,
    curva_de_massa,
    volumes_por_segmento,
)

SECAO = SecaoTransversal(
    largura_plataforma_m=10.0,
    talude_corte_h_v=1.0,
    talude_aterro_h_v=1.5,
)


def test_area_de_corte_soma_plataforma_e_taludes():
    """Altura 2 m: 10x2 do retângulo mais 1,0x2² dos taludes."""
    assert SECAO.area_corte(2.0) == pytest.approx(24.0)


def test_area_de_aterro_usa_o_talude_mais_suave():
    """Altura 2 m: 10x2 mais 1,5x2², maior que o corte equivalente."""
    assert SECAO.area_aterro(2.0) == pytest.approx(26.0)
    assert SECAO.area_aterro(2.0) > SECAO.area_corte(2.0)


def test_area_cresce_mais_que_proporcionalmente_a_altura():
    assert SECAO.area_corte(4.0) > 2 * SECAO.area_corte(2.0)


def test_altura_nula_ou_negativa_nao_gera_area():
    assert SECAO.area_corte(0.0) == 0.0
    assert SECAO.area_corte(-3.0) == 0.0
    assert SECAO.area_aterro(-3.0) == 0.0


def test_secao_recusa_talude_de_aterro_mais_ingreme():
    with pytest.raises(ValueError, match="mais íngreme"):
        SecaoTransversal(
            largura_plataforma_m=10.0,
            talude_corte_h_v=1.5,
            talude_aterro_h_v=1.0,
        )


def test_secao_recusa_largura_nao_positiva():
    with pytest.raises(ValueError, match="largura"):
        SecaoTransversal(
            largura_plataforma_m=0.0,
            talude_corte_h_v=1.0,
            talude_aterro_h_v=1.5,
        )


def _par(cotas_terreno: list[float], cotas_greide: list[float]):
    perfil = PerfilLongitudinal(
        estacoes=tuple(
            PontoPerfil(distancia_m=i * 100.0, cota_m=c)
            for i, c in enumerate(cotas_terreno)
        )
    )
    greide = Greide(
        estacoes=tuple(
            PontoPerfil(distancia_m=i * 100.0, cota_m=c)
            for i, c in enumerate(cotas_greide)
        )
    )
    return perfil, greide


def test_greide_acima_do_terreno_indica_aterro():
    perfil, greide = _par([700.0, 700.0], [703.0, 705.0])
    assert alturas_de_trabalho(perfil, greide) == pytest.approx((3.0, 5.0))


def test_greide_abaixo_do_terreno_indica_corte():
    perfil, greide = _par([710.0, 715.0], [706.0, 707.0])
    assert alturas_de_trabalho(perfil, greide) == pytest.approx((-4.0, -8.0))


def test_alturas_recusam_quantidades_diferentes_de_estacoes():
    perfil, _ = _par([700.0, 700.0, 700.0], [700.0, 700.0, 700.0])
    _, greide = _par([700.0, 700.0], [700.0, 700.0])
    with pytest.raises(ValueError, match="mesma quantidade"):
        alturas_de_trabalho(perfil, greide)


FATOR = 0.9


def test_corte_uniforme_gera_volume_previsivel():
    """Corte de 2 m em 100 m: área 24 m² por 100 m."""
    perfil, greide = _par([702.0, 702.0], [700.0, 700.0])
    volumes = calcular_volumes(perfil, greide, SECAO, FATOR)
    assert volumes.corte_m3 == pytest.approx(2400.0)
    assert volumes.aterro_m3 == 0.0


def test_aterro_uniforme_gera_volume_previsivel():
    perfil, greide = _par([700.0, 700.0], [702.0, 702.0])
    volumes = calcular_volumes(perfil, greide, SECAO, FATOR)
    assert volumes.aterro_m3 == pytest.approx(2600.0)
    assert volumes.corte_m3 == 0.0


def test_corte_aproveitavel_aplica_o_fator():
    perfil, greide = _par([702.0, 702.0], [700.0, 700.0])
    volumes = calcular_volumes(perfil, greide, SECAO, FATOR)
    assert volumes.corte_aproveitavel_m3 == pytest.approx(2160.0)


def test_saldo_positivo_indica_excesso_de_material():
    perfil, greide = _par([705.0, 705.0], [700.0, 700.0])
    assert calcular_volumes(perfil, greide, SECAO, FATOR).saldo_m3 > 0


def test_saldo_negativo_indica_falta_de_material():
    perfil, greide = _par([700.0, 700.0], [705.0, 705.0])
    assert calcular_volumes(perfil, greide, SECAO, FATOR).saldo_m3 < 0


def test_tracado_sem_movimentacao_e_compensado():
    perfil, greide = _par([700.0, 700.0], [700.0, 700.0])
    volumes = calcular_volumes(perfil, greide, SECAO, FATOR)
    assert volumes.movimentado_m3 == 0.0
    assert volumes.compensado is True


def test_curva_de_massa_comeca_em_zero():
    perfil, greide = _par([702.0, 702.0, 702.0], [700.0, 700.0, 700.0])
    assert curva_de_massa(perfil, greide, SECAO, FATOR)[0] == 0.0


def test_curva_de_massa_tem_uma_ordenada_por_estacao():
    perfil, greide = _par([702.0, 702.0, 702.0], [700.0, 700.0, 700.0])
    assert len(curva_de_massa(perfil, greide, SECAO, FATOR)) == len(perfil)


def test_curva_sobe_em_trecho_de_corte():
    perfil, greide = _par([702.0, 702.0, 702.0], [700.0, 700.0, 700.0])
    ordenadas = curva_de_massa(perfil, greide, SECAO, FATOR)
    assert ordenadas[2] > ordenadas[1] > ordenadas[0]


def test_curva_desce_em_trecho_de_aterro():
    perfil, greide = _par([700.0, 700.0, 700.0], [702.0, 702.0, 702.0])
    ordenadas = curva_de_massa(perfil, greide, SECAO, FATOR)
    assert ordenadas[2] < ordenadas[1] < ordenadas[0]


def test_um_par_de_volumes_por_segmento():
    perfil, greide = _par([702.0, 702.0, 702.0], [700.0, 700.0, 700.0])
    assert len(volumes_por_segmento(perfil, greide, SECAO)) == len(perfil) - 1


def test_fator_de_conversao_fora_da_faixa_e_recusado():
    perfil, greide = _par([702.0, 702.0], [700.0, 700.0])
    with pytest.raises(ValueError, match="fator de conversão"):
        calcular_volumes(perfil, greide, SECAO, 1.5)
