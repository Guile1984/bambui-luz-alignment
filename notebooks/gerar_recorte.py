"""Composição do recorte do modelo de elevação para o corredor de estudo.

Executado manualmente após o download dos tiles. Produz um arquivo
derivado em data/processed/, reconstruível a partir de data/raw/.
"""

from pathlib import Path

import rasterio

from bambui_luz.config.estudo import BAMBUI, ESTEIOS, LUZ, MARGEM_CORREDOR_M
from bambui_luz.infrastructure.mosaico import compor_recorte, extensao_com_margem

ORIGEM = Path("data/raw/mde")
DESTINO = Path("data/processed/mde_corredor.tif")


tiles = sorted(ORIGEM.glob("*.tif"))
print(f"Tiles de origem: {len(tiles)}")
for tile in tiles:
    print(f"  {tile.name}  ({tile.stat().st_size / 1024**2:.1f} MB)")


extensao = extensao_com_margem([BAMBUI, ESTEIOS, LUZ], MARGEM_CORREDOR_M)
oeste, sul, leste, norte = extensao
print("\nExtensão do recorte (graus):")
print(f"  longitude: {oeste:.4f} a {leste:.4f}")
print(f"  latitude:  {sul:.4f} a {norte:.4f}")


caminho = compor_recorte(tiles, extensao, DESTINO)
tamanho_mb = caminho.stat().st_size / 1024**2
print(f"\nRecorte gravado: {caminho}  ({tamanho_mb:.1f} MB)")


with rasterio.open(caminho) as raster:
    print(f"\nDimensões: {raster.width} x {raster.height} células")
    print(f"Sistema de referência: {raster.crs}")
    print(f"Valor de ausência: {raster.nodata}")
    print(f"Tipo de dado: {raster.dtypes[0]}")
    amostra = raster.read(1)
    print(f"\nCotas: mínima {amostra.min():.1f} m, máxima {amostra.max():.1f} m")
