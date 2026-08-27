"""Verifica a distribuição espacial das células com cota zero.

Hipótese: os zeros correspondem a área fora da cobertura dos tiles
baixados, não a dado ausente ou corpo d'água.
"""

from pathlib import Path

import numpy as np
import rasterio

CAMINHO = Path("data/processed/mde_corredor.tif")

with rasterio.open(CAMINHO) as raster:
    cotas = raster.read(1)
    transformacao = raster.transform

zeros = cotas == 0

por_coluna = zeros.sum(axis=0)
colunas_totalmente_zero = np.nonzero(por_coluna == cotas.shape[0])[0]
print(f"Colunas inteiramente zero: {len(colunas_totalmente_zero)}")
if len(colunas_totalmente_zero):
    print(
        f"  da coluna {colunas_totalmente_zero.min()} a {colunas_totalmente_zero.max()}"
    )
    lon, _ = rasterio.transform.xy(transformacao, 0, colunas_totalmente_zero.max())
    print(f"  última coluna zerada em longitude {lon:.5f}")

por_linha = zeros.sum(axis=1)
linhas_totalmente_zero = np.nonzero(por_linha == cotas.shape[1])[0]
print(f"\nLinhas inteiramente zero: {len(linhas_totalmente_zero)}")
for linha in linhas_totalmente_zero:
    _, lat = rasterio.transform.xy(transformacao, linha, 0)
    print(f"  linha {linha} em latitude {lat:.5f}")

restantes = int(zeros.sum()) - len(colunas_totalmente_zero) * cotas.shape[0]
restantes -= len(linhas_totalmente_zero) * cotas.shape[1]
print(f"\nZeros não explicados por linhas/colunas inteiras: {restantes:,}")
