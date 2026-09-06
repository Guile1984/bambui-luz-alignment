"""Baixa a máscara de corpos d'água que acompanha os tiles do Copernicus.

A máscara (WBM) identifica células classificadas como água, permitindo
verificar se um traçado percorre fundo de vale ou leito de curso d'água.

Dados de elevação Copernicus DEM.
"""

import urllib.request
from pathlib import Path

from bambui_luz.config.estudo import BAMBUI, ESTEIOS, LUZ
from bambui_luz.infrastructure.aquisicao import BASE_GLO30, tiles_necessarios

DESTINO = Path("data/raw/mascara_agua")
DESTINO.mkdir(parents=True, exist_ok=True)

coordenadas = [
    (local.latitude_graus, local.longitude_graus) for local in (BAMBUI, ESTEIOS, LUZ)
]

for nome in tiles_necessarios(coordenadas):
    sufixo = nome.replace("_DEM", "_WBM")
    url = f"{BASE_GLO30}/{nome}/AUXFILES/{sufixo}.tif"
    caminho = DESTINO / f"{sufixo}.tif"
    if caminho.exists():
        print(f"Já presente: {caminho.name}")
        continue
    print(f"Obtendo {sufixo}...")
    urllib.request.urlretrieve(url, caminho)
    print(f"  {caminho} ({caminho.stat().st_size / 1024**2:.1f} MB)")
