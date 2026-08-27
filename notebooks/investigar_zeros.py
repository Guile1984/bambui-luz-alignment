"""Investigação das células com cota zero no recorte de elevação.

Cota exatamente zero é implausível na região, cujo ponto mais baixo
conhecido está acima de 660 m. Este script quantifica e localiza a
ocorrência para decidir o tratamento.
"""

from pathlib import Path

import numpy as np
import rasterio

CAMINHO = Path("data/processed/mde_corredor.tif")

with rasterio.open(CAMINHO) as raster:
    cotas = raster.read(1)
    transformacao = raster.transform

total = cotas.size
zeros = cotas == 0
quantidade = int(zeros.sum())

print(f"Total de células: {total:,}")
print(f"Células com cota zero: {quantidade:,} ({100 * quantidade / total:.4f}%)")

if quantidade:
    linhas, colunas = np.nonzero(zeros)
    print(f"\nExtensão em linhas: {linhas.min()} a {linhas.max()}")
    print(f"Extensão em colunas: {colunas.min()} a {colunas.max()}")
    lon, lat = rasterio.transform.xy(transformacao, linhas[0], colunas[0])
    print(f"Primeira ocorrência: latitude {lat:.5f}, longitude {lon:.5f}")

abaixo_de_600 = cotas[(cotas > 0) & (cotas < 600)]
print(f"\nCélulas entre 0 600 m (exclusive): {abaixo_de_600.size:,}")
if abaixo_de_600.size:
    print(f"  faixa: {abaixo_de_600.min():.1f} a {abaixo_de_600.max():.1f} m")

validas = cotas[cotas > 0]
print(f"\nCotas acima de zero: {validas.min():.1f} a {validas.max():.1f} m")
print(f"Mediana: {np.median(validas):.1f} m")
