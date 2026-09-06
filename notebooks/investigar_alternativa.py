"""Investiga se a alternativa gerada percorre fundo de vale.

Hipótese: o caminho de menor custo desceu ao talvegue, onde a declividade
transversal é baixa, em vez de seguir os divisores de água. A superfície
de custo penaliza declividade e não distingue planalto de leito de curso
d'água.

Três verificações: distribuição de cotas, proximidade a corpos d'água e
posição relativa ao terreno vizinho.

Dados do OpenStreetMap (ODbL) e de elevação Copernicus DEM.
"""

import json
from pathlib import Path

import numpy as np
import rasterio

from bambui_luz.config.estudo import BAMBUI, ESTEIOS
from bambui_luz.infrastructure.malha_viaria import (
    caminho_mais_curto,
    montar_grafo,
    vertice_mais_proximo,
)

MDE = Path("data/processed/mde_corredor.tif")
REDE = Path("data/processed/rede_completa.geojson")
ALTERNATIVA = Path("data/processed/alternativa_menor_custo.geojson")
RAIO_VIZINHANCA = 15
"""Metade do lado da janela de vizinhança, em células (15 = cerca de 450 m)."""

grafo = montar_grafo(json.loads(REDE.read_text(encoding="utf-8")))
existente = caminho_mais_curto(
    grafo,
    vertice_mais_proximo(grafo, BAMBUI.longitude_graus, BAMBUI.latitude_graus),
    vertice_mais_proximo(grafo, ESTEIOS.longitude_graus, ESTEIOS.latitude_graus),
)
alternativa = json.loads(ALTERNATIVA.read_text(encoding="utf-8"))
coordenadas_alternativa = [
    tuple(c) for c in alternativa["features"][0]["geometry"]["coordinates"]
]

traçados = {
    "Existente (OSM)": existente,
    "Menor custo": coordenadas_alternativa,
}

with rasterio.open(MDE) as raster:
    cotas = raster.read(1)
    validas = cotas[cotas > 0]
    print(
        f"Corredor de estudo: cota mediana {np.median(validas):.1f} m, "
        f"faixa {validas.min():.1f} a {validas.max():.1f} m"
    )
    percentis = np.percentile(validas, [10, 25, 50, 75, 90])
    print(
        "Percentis do corredor: "
        + ", ".join(
            f"P{p}={v:.0f}"
            for p, v in zip([10, 25, 50, 75, 90], percentis, strict=False)
        )
    )

    for nome, coordenadas in traçados.items():
        celulas = [raster.index(lon, lat) for lon, lat in coordenadas]
        cotas_tracado = []
        posicoes = []
        for linha, coluna in celulas:
            if not (0 <= linha < raster.height and 0 <= coluna < raster.width):
                continue
            cota = float(cotas[linha, coluna])
            if cota <= 0:
                continue
            cotas_tracado.append(cota)

            l0 = max(0, linha - RAIO_VIZINHANCA)
            l1 = min(raster.height, linha + RAIO_VIZINHANCA + 1)
            c0 = max(0, coluna - RAIO_VIZINHANCA)
            c1 = min(raster.width, coluna + RAIO_VIZINHANCA + 1)
            janela = cotas[l0:l1, c0:c1]
            vizinhas = janela[janela > 0]
            if vizinhas.size:
                posicoes.append(cota - float(np.median(vizinhas)))

        arr_cotas = np.array(cotas_tracado)
        arr_pos = np.array(posicoes)
        print(f"\n=== {nome} ===")
        print(
            f"  cotas: mediana {np.median(arr_cotas):.1f} m, "
            f"faixa {arr_cotas.min():.1f} a {arr_cotas.max():.1f} m"
        )
        print(f"  posição relativa à vizinhança de {RAIO_VIZINHANCA * 30} m:")
        print(f"    mediana: {np.median(arr_pos):+.1f} m")
        print(f"    abaixo da vizinhança: {100 * (arr_pos < 0).mean():.1f}% dos pontos")
        print(f"    mais de 5 m abaixo: {100 * (arr_pos < -5).mean():.1f}% dos pontos")
        print(f"    mais de 5 m acima: {100 * (arr_pos > 5).mean():.1f}% dos pontos")
