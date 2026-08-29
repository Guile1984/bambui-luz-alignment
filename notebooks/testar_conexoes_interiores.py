"""Mede quantas conexões o modelo de grafo por extremos está perdendo.

Hipótese: no OSM, trechos se conectam também em vértices interiores, não
apenas nas pontas. Se muitos extremos coincidirem com pontos interiores de
outros trechos, o grafo precisa ser construído vértice a vértice.
"""

import json
from collections import Counter
from pathlib import Path

ORIGEM = Path("data/processed/malha_viaria.geojson")
CASAS_DECIMAIS = 5

colecao = json.loads(ORIGEM.read_text(encoding="utf-8"))


def chave(coordenada):
    return (round(coordenada[0], CASAS_DECIMAIS), round(coordenada[1], CASAS_DECIMAIS))


extremos = set()
interiores = set()
ocorrencias = Counter()

for feicao in colecao["features"]:
    coordenadas = feicao["geometry"]["coordinates"]
    extremos.add(chave(coordenadas[0]))
    extremos.add(chave(coordenadas[-1]))
    for coordenada in coordenadas[1:-1]:
        interiores.add(chave(coordenada))
    for coordenada in coordenadas:
        ocorrencias[chave(coordenada)] += 1

print(f"Pontos que são extremo de algum trecho: {len(extremos):,}")
print(f"Pontos que são interior de algum trecho: {len(interiores):,}")
print(f"Extremos que também são interior de outro: {len(extremos & interiores):,}")

compartilhados = {p: n for p, n in ocorrencias.items() if n > 1}
print(f"\nPontos presentes em mais de um trecho: {len(compartilhados):,}")
print(f"Total de pontos distintos: {len(ocorrencias):,}")
