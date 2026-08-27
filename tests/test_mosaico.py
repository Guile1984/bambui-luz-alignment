"""Testes da composição e recorte do modelo de elevação."""

import pytest

from bambui_luz.config.estudo import BAMBUI, ESTEIOS, LUZ
from bambui_luz.infrastructure.mosaico import extensao_com_margem


def test_extensao_contem_todos_os_locais():
    oeste, sul, leste, norte = extensao_com_margem([BAMBUI, ESTEIOS, LUZ], 5000.0)
    for local in (BAMBUI, ESTEIOS, LUZ):
        assert oeste < local.longitude_graus < leste
        assert sul < local.latitude_graus < norte


def test_margem_aumenta_a_extensao():
    sem_margem = extensao_com_margem([BAMBUI, LUZ], 0.0)
    com_margem = extensao_com_margem([BAMBUI, LUZ], 5000.0)
    assert com_margem[0] < sem_margem[0]
    assert com_margem[1] < sem_margem[1]
    assert com_margem[2] > sem_margem[2]
    assert com_margem[3] > sem_margem[3]


def test_margem_de_cinco_km_equivale_a_cerca_de_quatro_centesimos_de_grau():
    sem_margem = extensao_com_margem([BAMBUI], 0.0)
    com_margem = extensao_com_margem([BAMBUI], 5000.0)
    assert com_margem[3] - sem_margem[3] == pytest.approx(0.0449, abs=0.001)


def test_local_unico_gera_extensao_valida():
    oeste, sul, leste, norte = extensao_com_margem([BAMBUI], 1000.0)
    assert oeste < leste
    assert sul < norte


def test_extensao_exige_ao_menos_um_local():
    with pytest.raises(ValueError, match="ao menos um local"):
        extensao_com_margem([], 5000.0)
