"""Testes da construção do grafo viário."""

import pytest

from bambui_luz.infrastructure.malha_viaria import (
    caminho_mais_curto,
    montar_grafo,
    vertice_mais_proximo,
)


def _colecao(*geometrias, superficie="ground"):
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"surface": superficie},
                "geometry": {"type": "LineString", "coordinates": list(coords)},
            }
            for coords in geometrias
        ],
    }


def test_cada_segmento_vira_uma_aresta():
    grafo = montar_grafo(_colecao([[0.0, 0.0], [0.01, 0.0], [0.02, 0.0]]))
    assert grafo.number_of_edges() == 2
    assert grafo.number_of_nodes() == 3


def test_vias_conectam_em_vertice_interior():
    """Um trecho que termina no meio de outro compartilha o vértice."""
    grafo = montar_grafo(
        _colecao(
            [[0.0, 0.0], [0.01, 0.0], [0.02, 0.0]],
            [[0.01, 0.0], [0.01, 0.01]],
        )
    )
    assert grafo.number_of_nodes() == 4
    assert grafo.degree[(0.01, 0.0)] == 3


def test_extensao_da_aresta_e_positiva():
    grafo = montar_grafo(_colecao([[0.0, 0.0], [0.01, 0.0]]))
    for _, _, dados in grafo.edges(data=True):
        assert dados["extensao_m"] > 0


def test_revestimento_e_registrado_na_aresta():
    grafo = montar_grafo(_colecao([[0.0, 0.0], [0.01, 0.0]], superficie="asphalt"))
    for _, _, dados in grafo.edges(data=True):
        assert dados["superficie"] == "asphalt"


def test_colecao_vazia_e_recusada():
    with pytest.raises(ValueError, match="não contém feições"):
        montar_grafo({"type": "FeatureCollection", "features": []})


def test_vertice_mais_proximo_encontra_o_correto():
    grafo = montar_grafo(_colecao([[0.0, 0.0], [0.01, 0.0], [0.02, 0.0]]))
    assert vertice_mais_proximo(grafo, 0.0201, 0.0) == (0.02, 0.0)


def test_caminho_percorre_vertices_intermediarios():
    grafo = montar_grafo(_colecao([[0.0, 0.0], [0.01, 0.0], [0.02, 0.0]]))
    caminho = caminho_mais_curto(grafo, (0.0, 0.0), (0.02, 0.0))
    assert caminho == [(0.0, 0.0), (0.01, 0.0), (0.02, 0.0)]


def test_componentes_distintos_recusam_caminho():
    grafo = montar_grafo(_colecao([[0.0, 0.0], [0.01, 0.0]], [[0.5, 0.5], [0.51, 0.5]]))
    with pytest.raises(ValueError, match="componentes distintos"):
        caminho_mais_curto(grafo, (0.0, 0.0), (0.5, 0.5))
