"""Testes do contrato de acesso a elevação."""

from collections.abc import Sequence

import pytest

from bambui_luz.domain.geometria import Ponto
from bambui_luz.ports.elevacao import ElevacaoIndisponivelError, ProvedorElevacao


class ProvedorPlanoInclinado:
    """Provedor sintético: cota cresce 5 m a cada 100 m de Este.

    Cobre apenas o primeiro quadrante, entre 0 e 1000 m em cada eixo.
    """

    LIMITE_M = 1000.0

    def cotas_em(self, pontos: Sequence[Ponto]) -> tuple[float, ...]:
        cotas = []
        for ponto in pontos:
            if not (0 <= ponto.x <= self.LIMITE_M and 0 <= ponto.y <= self.LIMITE_M):
                raise ElevacaoIndisponivelError(
                    f"ponto fora da cobertura: ({ponto.x}, {ponto.y})"
                )
            cotas.append(700.0 + ponto.x * 0.05)
        return tuple(cotas)


def test_provedor_sintetico_satisfaz_o_contrato():
    assert isinstance(ProvedorPlanoInclinado(), ProvedorElevacao)


def test_cotas_seguem_a_ordem_dos_pontos():
    pontos = [Ponto(x=0.0, y=0.0), Ponto(x=200.0, y=0.0), Ponto(x=100.0, y=0.0)]
    assert ProvedorPlanoInclinado().cotas_em(pontos) == pytest.approx(
        (700.0, 710.0, 705.0)
    )


def test_resultado_tem_o_mesmo_comprimento_da_entrada():
    pontos = [Ponto(x=float(i), y=0.0) for i in range(10)]
    assert len(ProvedorPlanoInclinado().cotas_em(pontos)) == len(pontos)


def test_ponto_fora_da_cobertura_levanta_erro():
    with pytest.raises(ElevacaoIndisponivelError, match="fora da cobertura"):
        ProvedorPlanoInclinado().cotas_em([Ponto(x=5000.0, y=0.0)])


def test_lote_vazio_devolve_tupla_vazia():
    assert ProvedorPlanoInclinado().cotas_em([]) == ()
