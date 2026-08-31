"""Geração da primeira alternativa de traçado por menor custo.

Compõe a superfície de custo a partir do modelo de elevação e busca o
caminho de menor custo acumulado entre Bambuí e Esteios.

O resultado é um corredor de estudo, não um eixo geométrico: o caminho
avança por células de 30 m em oito direções possíveis.

Dados de elevação Copernicus DEM.
"""

import json
from pathlib import Path

import numpy as np
import rasterio

from bambui_luz.config.estudo import (
    BAMBUI,
    CUSTO_BARREIRA,
    DECLIVIDADE_BARREIRA_PCT,
    DECLIVIDADE_REFERENCIA_PCT,
    ESTEIOS,
    PESO_DECLIVIDADE,
)
from bambui_luz.infrastructure.superficie import (
    calcular_declividade,
    compor_custo,
    dimensoes_celula_m,
)
from bambui_luz.infrastructure.tracado_otimo import caminho_de_menor_custo

MDE = Path("data/processed/mde_corredor.tif")
DESTINO = Path("data/processed/alternativa_menor_custo.geojson")

with rasterio.open(MDE) as raster:
    cotas = raster.read(1)
    transformacao = raster.transform
    origem_celula = raster.index(BAMBUI.longitude_graus, BAMBUI.latitude_graus)
    destino_celula = raster.index(ESTEIOS.longitude_graus, ESTEIOS.latitude_graus)
    latitude_media = raster.bounds.bottom + (raster.bounds.top - raster.bounds.bottom)

largura_m, altura_m = dimensoes_celula_m(
    abs(transformacao.a), abs(transformacao.e), latitude_media
)
print(f"Célula: {largura_m:.1f} m (leste-oeste) x {altura_m:.1f} m (norte-sul)")

declividade = calcular_declividade(cotas, largura_m, altura_m)
validas = declividade[~np.isnan(declividade)]
print("\nDeclividade do corredor:")
print(f"  mediana: {np.median(validas):.1f}%")
print(f"  percentil 90: {np.percentile(validas, 90):.1f}%")
print(f"  máxima:   {validas.max():.1f}%")
print(
    f"  acima de   {DECLIVIDADE_BARREIRA_PCT:.0f}%: "
    f"{100 * (validas > DECLIVIDADE_BARREIRA_PCT).mean():.1f}% das células"
)

custo = compor_custo(
    declividade,
    DECLIVIDADE_REFERENCIA_PCT,
    PESO_DECLIVIDADE,
    DECLIVIDADE_BARREIRA_PCT,
    CUSTO_BARREIRA,
)

print(f"\nOrigem (Bambuí):  célula {origem_celula}")
print(f"Destino (Esteios):  célula {destino_celula}")

caminho, custo_total = caminho_de_menor_custo(custo, origem_celula, destino_celula)
print(f"\nCélulas no caminho: {len(caminho):,}")
print(f"Custo acumulado: {custo_total:,.0f}")

coordenadas = [
    list(rasterio.transform.xy(transformacao, linha, coluna))
    for linha, coluna in caminho
]

DESTINO.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "nome": "alternativa por menor custo",
                        "peso_declividade": PESO_DECLIVIDADE,
                        "declividade_referencia_pct": DECLIVIDADE_REFERENCIA_PCT,
                        "declividade_barreira_pct": DECLIVIDADE_BARREIRA_PCT,
                    },
                    "geometry": {"type": "LineString", "coordinates": coordenadas},
                }
            ],
        }
    ),
    encoding="utf-8",
)
print(f"Gravado: {DESTINO}")
