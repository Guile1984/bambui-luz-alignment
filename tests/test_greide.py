"""Testes da geração e verificação do greide."""

import pytest

from bambui_luz.domain.greide import Greide, suavizar
from bambui_luz.domain.perfil import PerfilLongitudinal, PontoPerfil
from bambui_luz.domain.rodovia import ClasseRodovia

CLASSE = ClasseRodovia(
    nome="classe de teste",
    velocidade_diretriz_kmh=60.0,
    rampa_maxima_pct=6.0,
    fonte="valor de exemplo, sem vínculo normativo",
)


def _perfil(cotas: list[float], passo_m: float = 100.0) -> PerfilLongitudinal:
    return PerfilLongitudinal(
        estacoes=tuple(
            PontoPerfil(distancia_m=indice * passo_m, cota_m=cota)
            for indice, cota in enumerate(cotas)
        )
    )


def test_greide_preserva_as_distancias_do_perfil():
    perfil = _perfil([700.0, 710.0, 700.0, 710.0, 700.0])
    greide = suavizar(perfil, janela_m=300.0)
    assert [e.distancia_m for e in greide.estacoes] == [
        e.distancia_m for e in perfil.estacoes
    ]


def test_greide_sobre_terreno_plano_coincide_com_ele():
    perfil = _perfil([700.0] * 5)
    greide = suavizar(perfil, janela_m=300.0)
    assert [e.cota_m for e in greide.estacoes] == pytest.approx([700] * 5)


def test_greide_sobre_rampa_constante_preserva_a_rampa():
    """A média móvel de uma reta é a própria reta, excete nas bordas."""
    perfil = _perfil([700.0, 703.0, 706.0, 709.0, 712.0])
    greide = suavizar(perfil, janela_m=200.0)
    assert greide.rampas()[1:-1] == pytest.approx([3.0, 3.0])


def test_suavizacao_reduz_a_rampa_maxima():
    perfil = _perfil([700.0, 715.0, 700.0, 715.0, 700.0])
    greide = suavizar(perfil, janela_m=400.0)
    assert greide.rampa_maxima_absoluta < perfil.rampa_maxima_absoluta


def test_janela_maior_suaviza_mais():
    perfil = _perfil([700.0, 715.0, 700.0, 715.0, 700.0, 715.0, 700.0])
    curta = suavizar(perfil, janela_m=200.0)
    longa = suavizar(perfil, janela_m=600.0)
    assert longa.rampa_maxima_absoluta < curta.rampa_maxima_absoluta


def test_segmentos_inadmissiveis_sao_localizados():
    perfil = _perfil([700.0, 720, 740.0])
    greide = suavizar(perfil, janela_m=100.0)
    assert len(greide.segmentos_inadmissiveis(CLASSE)) == 2


def test_greide_suave_nao_tem_segmento_inadmissivel():
    perfil = _perfil([700.0, 702.0, 704.0])
    greide = suavizar(perfil, janela_m=100.0)
    assert greide.segmentos_inadmissiveis(CLASSE) == ()


def test_janela_nao_positiva_e_recusada():
    with pytest.raises(ValueError, match="positiva"):
        suavizar(_perfil([700.0, 710.0]), janela_m=0.0)


def test_greide_exige_tupla():
    with pytest.raises(TypeError, match="tupla"):
        Greide(estacoes=[PontoPerfil(distancia_m=0.0, cota_m=700.0)])


def test_greide_exige_duas_estacoes():
    with pytest.raises(ValueError, match="duas estações"):
        Greide(estacoes=(PontoPerfil(distancia_m=0.0, cota_m=700.0),))
