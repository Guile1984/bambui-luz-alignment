"""Construção do grafo viário a partir de geometria do OpenStreetMap.

O grafo é montado vértice a vértice, e não pelos extremos de cada trecho:
vias se conectam também em pontos interiores, e um grafo por extremos
perde essas junções.

As coordenadas são arredondadas para formar as chaves de vértice. A
tolerância adotada corresponde a cerca de um metro, suficiente para unir
pontos que representam o mesmo nó de origem sem fundir vias distintas que
apenas passam próximas.

Dados do OpenStreetMap, disponibilizados sob ODbL.
"""

from itertools import pairwise

import networkx as nx
from pyproj import Geod

CASAS_DECIMAIS_VERTICE = 5
"""Arredondamento das coordenadas ao formar vértices: cerca de 1 m."""

ELIPSOIDE = "GRS80"
"""Elipsoide de referÊncia para o cálculo de distâncias."""


def _chave(coordenada: list[float]) -> tuple[float, float]:
    """Converte uma coordenada em chave de vértice, com tolerância."""
    return (
        round(coordenada[0], CASAS_DECIMAIS_VERTICE),
        round(coordenada[1], CASAS_DECIMAIS_VERTICE),
    )


def montar_grafo(colecao: dict) -> nx.MultiGraph:
    """Monta o grafo viário a partir de uma coleção de feições GeoJSON.

    Cada segmento entre vértices consecutivos torna-se uma aresta, com a
    extensão geodésica como peso e o revestimento como atributo.

    Args:
        colecao: Coleção GeoJSON com feições de linha.

    Returns:
        Grafo com múltiplas arestas admitidas entre o mesmo par de
        vértices, pois vias distintas podem ligar os mesmos pontos.

    Raises:
        ValueError: Se a coleção não contiver feições.
    """
    feicoes = colecao.get("features", [])
    if not feicoes:
        raise ValueError("a coleção não contém feições")

    geodesico = Geod(ellps=ELIPSOIDE)
    grafo = nx.MultiGraph()
    for feicao in feicoes:
        coordenadas = feicao["geometry"]["coordinates"]
        superficie = feicao.get("properties", {}).get("surface", "(sem tag)")
        for anterior, atual in pairwise(coordenadas):
            _, _, extensao = geodesico.inv(anterior[0], anterior[1], atual[0], atual[1])
            grafo.add_edge(
                _chave(anterior),
                _chave(atual),
                extensao_m=extensao,
                superficie=superficie,
            )
    return grafo


def vertice_mais_proximo(
    grafo: nx.MultiGraph, longitude_graus: float, latitude_graus: float
) -> tuple[float, float]:
    """Encontra o vértie do grafo mais próximo de uma coordenada.

    Args:
        grafo: Grafo viário.
        longitude_graus: Longitude em graus decimais.
        latitude_graus: Latitude em graus decimais.

    Returns:
        Coordenadas do vértice mais próximo.

    Raises:
        ValueError: Se o grafo não tiver vértices.
    """
    if grafo.number_of_nodes() == 0:
        raise ValueError("o grafo não contém vértices")
    geodesico = Geod(ellps=ELIPSOIDE)
    melhor, menor = None, float("inf")
    for no in grafo.nodes:
        _, _, distancia = geodesico.inv(longitude_graus, latitude_graus, no[0], no[1])
        if distancia < menor:
            melhor, menor = no, distancia
    return melhor


def caminho_mais_curto(
    grafo: nx.MultiGraph,
    origem: tuple[float, float],
    destino: tuple[float, float],
) -> list[tuple[float, float]]:
    """Encontra o caminho de menor extensão entre dois vértices.

    Args:
        grafo: Grafo viário.
        origem: Vértice inicial.
        destino: Vértice final.

    Returns:
        Sequência de vértices percorridos.

    Raises:
        ValueError: Se não houver caminho entre os vértices.
    """
    if not nx.has_path(grafo, origem, destino):
        raise ValueError(
            f"não há caminho contínuo entre {origem} e {destino}: "
            "os vértices pertencem a componentes distintos"
        )
    return nx.shortest_path(grafo, origem, destino, weight="extensao_m")
