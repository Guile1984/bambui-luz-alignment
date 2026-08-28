"""Download da geometria viária do corredor Bambuí-Esteios.

Obtém ways com coordenadas e grava em GeoJSON para inspeção. O arquivo é
derivado e não versionado: dados do OpenStreetMap são disponibilizados sob
ODbL, que impõe compartilhamento nos mesmos termos a bases derivadas.

Dados do OpenStreetMap, disponibilizados sob ODbL.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

from bambui_luz.config.estudo import BAMBUI, ESTEIOS
from bambui_luz.infrastructure.mosaico import extensao_com_margem

OVERPASS = "https://overpass-api.de/api/interpreter"
IDENTIFICACAO = (
    "bambui-luz-alignment/0.1 (https://github.com/Guile1984/bambui-luz-alignment)"
)
CLASSES_RURAIS = "primary|secondary|tertiary|unclassified|track|road"
DESTINO = Path("data/processed/malha_viaria.geojson")

oeste, sul, leste, norte = extensao_com_margem([BAMBUI, ESTEIOS], 2000.0)

consulta = f"""
[out:json][timeout:180];
way["highway"~"^({CLASSES_RURAIS})$"]["surface"~"^(unpaved|ground|dirt|gravel|compacted|fine_gravel)$"]({sul},{oeste},{norte},{leste});
out geom;
"""

print("Consultando a Overpass...")
dados = urllib.parse.urlencode({"data": consulta}).encode("utf-8")
requisicao = urllib.request.Request(
    OVERPASS, data=dados, headers={"User-Agent": IDENTIFICACAO}
)
try:
    with urllib.request.urlopen(requisicao, timeout=240) as resposta:
        resultado = json.load(resposta)
except urllib.error.HTTPError as erro:
    print(f"HTTP {erro.code} - resposta do servidor:\n")
    print(erro.read().decode("utf-8", errors="replace")[:3000])
    raise

elementos = [e for e in resultado["elements"] if e.get("geometry")]
print(f"Trechos com geometria: {len(elementos)}")

feicoes = []

total_vertices = 0
for elemento in elementos:
    coordenadas = [[p["lon"], p["lat"]] for p in elemento["geometry"]]
    total_vertices += len(coordenadas)
    feicoes.append(
        {
            "type": "Feature",
            "id": elemento["id"],
            "properties": elemento.get("tags", {}),
            "geometry": {"type": "LineString", "coordinates": coordenadas},
        }
    )

colecao = {"type": "FeatureCollection", "features": feicoes}
DESTINO.parent.mkdir(parents=True, exist_ok=True)
DESTINO.write_text(json.dumps(colecao), encoding="utf-8")

tamanho_mb = DESTINO.stat().st_size / 1024**2
print(f"Vértices no total: {total_vertices:,}")
print(f"Gravado: {DESTINO} ({tamanho_mb:.1f} MB)")

por_superficie = defaultdict(int)
for feicao in feicoes:
    por_superficie[feicao["properties"].get("surface", "(sem tag)")] += 1

print("\nRevestimento dos trechos com geometria:")
for superficie, quantidade in sorted(por_superficie.items(), key=lambda i: -i[1]):
    print(f"  {superficie:<15} {quantidade:>4}")
