"""Download dos tiles de elevação necessários ao corredor de estudo.

Executado manualmente. Os arquivos vão para data/raw/, fora do controle de
versão. Repetir a execução não rebaixa arquivos já presentes.
"""

from pathlib import Path

from bambui_luz.config.estudo import BAMBUI, ESTEIOS, LUZ
from bambui_luz.infrastructure.aquisicao import baixar_tile, tiles_necessarios

DESTINO = Path("data/raw/mde")

coordenadas = [
    (local.latitude_graus, local.longitude_graus) for local in (BAMBUI, ESTEIOS, LUZ)
]

for nome in tiles_necessarios(coordenadas):
    print(f"Obtendo {nome}")
    caminho = baixar_tile(nome, DESTINO)
    tamanho_mb = caminho.stat().st_size / 1024**2
    print(f"  {caminho}  ({tamanho_mb:.1f} MB)")
