"""Desenha a alternativa gerada e o traçado existente sobre a declividade.

Dados do OpenStreetMap (ODbL) e de elevação Copernicus DEM.
"""

import json
from itertools import pairwise
from pathlib import Path

import networkx as nx
import rasterio
from pyproj import Geod

from bambui_luz.config.estudo import BAMBUI, ESTEIOS
from bambui_luz.infrastructure.superficie import (
    calcular_declividade,
    dimensoes_celula_m,
)
from bambui_luz.presentation.mapa_tracados import desenhar_mapa

MDE = Path("data/processed/mde_corredor.tif")
REDE = Path("data/processed/rede_completa.geojson")
ALTERNATIVA = Path("data/processed/alternativa_menor_custo.geojson")
DESTINO = Path("data/processed/mapa_comparativo.png")
CASAS_DECIMAIS = 5


with rasterio.open(MDE) as raster:
    cotas = raster.read(1)
    transformacao = raster.transform
    limites = raster.bounds

latitude_media = (limites.bottom + limites.top) / 2
largura_m, altura_m = dimensoes_celula_m(
    abs(transformacao.a), abs(transformacao.e), latitude_media
)
declividade = calcular_declividade(cotas, largura_m, altura_m)

geodesico = Geod(ellps="GRS80")
colecao = json.loads(REDE.read_text(encoding="utf-8"))
grafo = nx.MultiGraph()
for feicao in colecao["features"]:
    coordenadas = feicao["geometry"]["coordinates"]
    for anterior, atual in pairwise(coordenadas):
        _, _, extensao = geodesico.inv(anterior[0], anterior[1], atual[0], atual[1])
        grafo.add_edge(
            (round(anterior[0], CASAS_DECIMAIS), round(anterior[1], CASAS_DECIMAIS)),
            (round(atual[0], CASAS_DECIMAIS), round(atual[1], CASAS_DECIMAIS)),
            extensao_m=extensao,
        )


def mais_proximo(longitude, latitude):
    melhor, menor = None, float("inf")
    for no in grafo.nodes:
        _, _, distancia = geodesico.inv(longitude, latitude, no[0], no[1])
        if distancia < menor:
            melhor, menor = no, distancia
    return melhor


existente = nx.shortest_path(
    grafo,
    mais_proximo(BAMBUI.longitude_graus, BAMBUI.latitude_graus),
    mais_proximo(ESTEIOS.longitude_graus, ESTEIOS.latitude_graus),
    weight="extensao_m",
)

alternativa = json.loads(ALTERNATIVA.read_text(encoding="utf-8"))
coordenadas_alternativa = alternativa["features"][0]["geometry"]["coordinates"]

caminho = desenhar_mapa(
    fundo=declividade,
    extensao=(limites.left, limites.right, limites.bottom, limites.top),
    tracados={
        "Traçado existente (OSM)": existente,
        "Alternativa por menor custo": [tuple(c) for c in coordenadas_alternativa],
    },
    pontos={
        "Bambuí": (BAMBUI.longitude_graus, BAMBUI.latitude_graus),
        "Esteios": (ESTEIOS.longitude_graus, ESTEIOS.latitude_graus),
    },
    destino=DESTINO,
    titulo="Alternativa gerada e traçado existente sobre a declividade do terreno",
)
print(f"Mapa gravado: {caminho}")
