"""Análise da conectividade da malha não pavimentada.

Cada segmento entre vértices consecutivos é uma aresta, e não cada trecho
inteiro: no OSM, vias se conectam também em vértices interiores, e um
grafo montado apenas pelos extremos perde essas junções.

Dados do OpenStreetMap, disponibilizados sob ODbL.
"""

import json
from collections import defaultdict
from itertools import pairwise
from pathlib import Path

import networkx as nx
from pyproj import Geod

from bambui_luz.config.estudo import BAMBUI, ESTEIOS

ORIGEM = Path("data/processed/rede_completa.geojson")
CASAS_DECIMAIS = 5
"""Arredondamento das coordenadas ao formar vértices: cerca de 1 m."""

geodesico = Geod(ellps="GRS80")
colecao = json.loads(ORIGEM.read_text(encoding="utf-8"))


def vertice(coordenada: list[float]) -> tuple[float, float]:
    """Converte uma coordenada em chave de vértice, com tolerância."""
    return (round(coordenada[0], CASAS_DECIMAIS), round(coordenada[1], CASAS_DECIMAIS))


grafo = nx.MultiGraph()
for feicao in colecao["features"]:
    coordenadas = feicao["geometry"]["coordinates"]
    id_osm = feicao["id"]
    superficie = feicao["properties"].get("surface", "(sem tag)")
    for anterior, atual in pairwise(coordenadas):
        _, _, extensao = geodesico.inv(anterior[0], anterior[1], atual[0], atual[1])
        grafo.add_edge(
            vertice(anterior),
            vertice(atual),
            extensao_m=extensao,
            id_osm=id_osm,
            superficie=superficie,
        )

print(f"Vértices: {grafo.number_of_nodes():,}")
print(f"Arestas: {grafo.number_of_edges():,}")

extensao_total = sum(d["extensao_m"] for _, _, d in grafo.edges(data=True))
print(f"Extensão total da malha: {extensao_total / 1000:.1f} km")

componentes = sorted(nx.connected_components(grafo), key=len, reverse=True)
print(f"\nComponentes conexos: {len(componentes)}")
print("Cinco maiores, por número de vértices:")
for indice, componente in enumerate(componentes[:5]):
    subgrafo = grafo.subgraph(componente)
    km = sum(d["extensao_m"] for _, _, d in subgrafo.edges(data=True)) / 1000
    print(f"  {indice}: {len(componente):>5} vértices, {km:>7.1f} km")


def vertice_mais_proximo(longitude: float, latitude: float) -> tuple:
    """Encontra o vértice do grafo mais próximo de uma coordenada."""
    melhor, menor = None, float("inf")
    for no in grafo.nodes:
        _, _, distancia = geodesico.inv(longitude, latitude, no[0], no[1])
        if distancia < menor:
            melhor, menor = no, distancia
    return melhor, menor


print("\nVértices mais próximos das localidades:")
posicoes = {}
for local in (BAMBUI, ESTEIOS):
    no, distancia = vertice_mais_proximo(local.longitude_graus, local.latitude_graus)
    indice = next(i for i, c in enumerate(componentes) if no in c)
    posicoes[local.nome] = (no, indice)
    print(
        f"  {local.nome}: a {distancia / 1000:.2f} km do vértice "
        f"({no[0]:.5f}, {no[1]:.5f}), no componente {indice}"
    )

no_bambui, comp_bambui = posicoes["Bambuí"]
no_esteios, comp_esteios = posicoes["Esteios"]

if comp_bambui != comp_esteios:
    print(
        f"\nSem caminho contínuo: Bambuí no componente {comp_bambui}, "
        f"Esteios no componente {comp_esteios}"
    )
else:
    caminho = nx.shortest_path(grafo, no_bambui, no_esteios, weight="extensao_m")
    extensao_caminho = nx.shortest_path_length(
        grafo, no_bambui, no_esteios, weight="extensao_m"
    )
    print(f"\nCaminho encontrado: {extensao_caminho / 1000:.2f} km")
    print(f"Vértices no caminho: {len(caminho):,}")

    por_superficie = defaultdict(float)
    for anterior, atual in pairwise(caminho):
        dados = min(grafo[anterior][atual].values(), key=lambda d: d["extensao_m"])
        por_superficie[dados["superficie"]] += dados["extensao_m"]

    print("\nRevestimento ao longo do caminho:")
    for superficie, metros in sorted(por_superficie.items(), key=lambda i: -i[1]):
        pct = 100 * metros / extensao_caminho
        print(f"  {superficie:<15} {metros / 1000:>7.2f} km  ({pct:>5.1f}%)")
