"""Testes da geração de traçados por menor custo."""

from itertools import pairwise

import numpy as np
import pytest

from bambui_luz.infrastructure.tracado_otimo import caminho_de_menor_custo


def test_caminho_em_grade_uniforme_segue_a_reta():
    custo = np.ones((5, 5))
    caminho, _ = caminho_de_menor_custo(custo, (0, 0), (0, 4))
    assert caminho[0] == (0, 0)
    assert caminho[-1] == (0, 4)
    assert len(caminho) == 5


def test_caminho_contorna_a_barreira():
    """Uma parede cara na coluna central força o desvio pela abertura."""
    custo = np.ones((5, 5))
    custo[0:4, 2] = 1000.0
    caminho, _ = caminho_de_menor_custo(custo, (0, 0), (0, 4))
    assert (4, 2) in caminho or (3, 2) not in caminho
    assert caminho[-1] == (0, 4)


def test_celulas_sao_sempre_adjacentes():
    custo = np.random.default_rng(42).uniform(1.0, 10.0, size=(10, 10))
    caminho, _ = caminho_de_menor_custo(custo, (0, 0), (9, 9))
    for anterior, atual in pairwise(caminho):
        assert abs(atual[0] - anterior[0]) <= 1
        assert abs(atual[1] - anterior[1]) <= 1


def test_custo_total_e_positivo():
    custo = np.ones((5, 5))
    _, total = caminho_de_menor_custo(custo, (0, 0), (4, 4))
    assert total > 0


def test_origem_fora_da_grade_e_recusada():
    with pytest.raises(ValueError, match="origem fora"):
        caminho_de_menor_custo(np.ones((3, 3)), (5, 0), (0, 0))


def test_destino_fora_da_grade_e_recusado():
    with pytest.raises(ValueError, match="destino fora"):
        caminho_de_menor_custo(np.ones((3, 3)), (0, 0), (0, 7))


def test_grade_com_indeterminacao_e_recusada():
    custo = np.ones((3, 3))
    custo[1, 1] = np.nan
    with pytest.raises(ValueError, match="indeterminados"):
        caminho_de_menor_custo(custo, (0, 0), (2, 2))


def test_grade_com_custo_negativo_e_recusada():
    custo = np.ones((3, 3))
    custo[1, 1] = -5.0
    with pytest.raises(ValueError, match="negativos"):
        caminho_de_menor_custo(custo, (0, 0), (2, 2))
