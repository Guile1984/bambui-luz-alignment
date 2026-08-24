"""Exploração do Cadastro de Localidades Selecionadas do IBGE.

Script descartável, executado uma única vez para extrair as coordenadas
das localidades de interesse. O resultado é transcrito para
bambui_luz/config/estudo.py como constantes com fonte declarada.
"""

from pathlib import Path

import geopandas as gpd

CAMINHO = Path("data/raw/BR_Localidades_2010_v1.shp")
UF = "MINAS GERAIS"
MUNICIPIOS = ["BAMBUÍ", "LUZ"]
COLUNAS = ["NM_LOCALID", "NM_MUNICIP", "NM_CATEGOR", "LONG", "LAT", "ALT"]

localidades = gpd.read_file(CAMINHO)
print(f"Sistema de referência: {localidades.crs}")

recorte = localidades[
    (localidades["NM_UF"] == UF) & (localidades["NM_MUNICIP"].isin(MUNICIPIOS))
]

if recorte.empty:
    print("Nenhum registro encontrado. Municípios disponíveis contendo 'BAMB': ")
    candidatos = localidades[localidades["NM_MUNICIP"].str.contains("BAMB", na=False)]
    print(candidatos["NM_MUNICIP"].unique())
else:
    print(f"\n{len(recorte)} localidades encontradas:\n")
    print(recorte[COLUNAS].to_string(index=False))
