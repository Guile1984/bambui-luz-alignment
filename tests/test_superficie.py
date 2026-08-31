"""Testes das superfícies derivadas do modelo de elevação."""

import numpy as np
import pytest

from bambui_luz.infrastructure.superficie import (
    calcular_declividade,
    compor_custo,
    dimensoes_celula_m,
)

CELULA_M = 30.0


def test_terreno_plano_tem_declividade_nula():
    cotas = np.full((5, 5), 700.0)
    declividade = calcular_declividade(cotas, CELULA_M, CELULA_M)
    assert declividade == pytest.approx(np.zeros((5, 5)))


def test_plano_inclinado_em_leste_oeste():
    """Cota cresce 3 m por célula de 30 m: declividade de 10%."""
    cotas = np.tile(np.arange(5) * 3.0 + 700.0, (5, 1))
    declividade = calcular_declividade(cotas, CELULA_M, CELULA_M)
    assert declividade == pytest.approx(np.full((5, 5), 10.0))


def test_plano_inclinado_em_norte_sul():
    cotas = np.tile((np.arange(5) * 3.0 + 700.0).reshape(-1, 1), (1, 5))
    declividade = calcular_declividade(cotas, CELULA_M, CELULA_M)
    assert declividade == pytest.approx(np.full((5, 5), 10.0))


def test_inclinacao_diagonal_compoe_as_duas_direcoes():
    linhas, colunas = np.meshgrid(np.arange(5), np.arange(5), indexing="ij")
    cotas = 700.0 + 3.0 * linhas + 3.0 * colunas
    declividade = calcular_declividade(cotas, CELULA_M, CELULA_M)
    assert declividade == pytest.approx(np.full((5, 5), np.hypot(10.0, 10.0)))


def test_celula_nao_quadrada_usa_dimensao_correta_em_cada_direcao():
    cotas = np.tile(np.arange(5) * 3.0 + 700.0, (5, 1))
    declividade = calcular_declividade(cotas, 15.0, 30.0)
    assert declividade == pytest.approx(np.full((5, 5), 20.0))


def test_celula_ausente_propaga_indeterminacao():
    cotas = np.full((5, 5), 700.0)
    cotas[2, 2] = 0.0
    declividade = calcular_declividade(cotas, CELULA_M, CELULA_M)
    assert np.isnan(declividade[2, 2])
    assert np.isnan(declividade[2, 1])
    assert not np.isnan(declividade[0, 0])


def test_dimensoes_de_celula_rejeitam_valor_nao_positivo():
    with pytest.raises(ValueError, match="positivas"):
        calcular_declividade(np.full((3, 3), 700.0), 0.0, 30.0)


def test_celula_de_um_segundo_de_arco_na_latitude_do_estudo():
    """Um segundo de arco a 20 graus sul: cerca de 29 m por 31 m."""
    largura, altura = dimensoes_celula_m(1 / 3600, 1 / 3600, -20.0)
    assert largura == pytest.approx(29.0, abs=0.5)
    assert altura == pytest.approx(30.8, abs=0.5)
    assert altura > largura


REFERENCIA_PCT = 10.0
PESO = 4.0
BARREIRA_PCT = 25.0
CUSTO_BARREIRA = 1000.0


def _custo(declividade: np.ndarray) -> np.ndarray:
    return compor_custo(declividade, REFERENCIA_PCT, PESO, BARREIRA_PCT, CUSTO_BARREIRA)


def test_terreno_plano_tem_custo_unitario():
    assert _custo(np.zeros((3, 3))) == pytest.approx(np.ones((3, 3)))


def test_declividade_de_referencia_custa_o_peso_mais_a_base():
    assert _custo(np.full((2, 2), 10.0)) == pytest.approx(np.full((2, 2), 5.0))


def test_custo_cresce_com_o_quadrado_da_declividade():
    """Dobrar a declividade quadruplica a parcela de penalidade."""
    simples = _custo(np.array([[10.0]]))[0, 0] - 1.0
    dobro = _custo(np.array([[20.0]]))[0, 0] - 1.0
    assert dobro == pytest.approx(4 * simples)


def test_acima_da_barreira_o_custo_e_proibitivo():
    assert _custo(np.array([[30.0]]))[0, 0] == pytest.approx(CUSTO_BARREIRA)


def test_declividade_independente_recebe_custo_de_barreira():
    assert _custo(np.array([[np.nan]]))[0, 0] == pytest.approx(CUSTO_BARREIRA)


def test_custo_nunca_e_indeterminado():
    declividade = np.array([[0.0, 5.0], [np.nan, 40.0]])
    assert not np.isnan(_custo(declividade)).any()


def test_referencia_nao_positiva_e_recusada():
    with pytest.raises(ValueError, match="referência"):
        compor_custo(np.zeros((2, 2)), 0.0, PESO, BARREIRA_PCT, CUSTO_BARREIRA)


def test_custo_de_barreira_deve_superar_o_custo_base():
    with pytest.raises(ValueError, match="barreira"):
        compor_custo(np.zeros((2, 2)), REFERENCIA_PCT, PESO, BARREIRA_PCT, 0.5)
