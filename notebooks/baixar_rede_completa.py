"""Download da rede viária completa no corredor Bambuí-Esteios.

Sem filtro de revestimento: a análise anterior mostrou que filtrar por
surface na consulta quebra a conectividade, pois o percurso real é misto
(pavimentado nas saídas urbanas, leito natural no meio). A classificação
por revestimento passa a ser feita na análise, não na consulta.

A caixa cobre apenas os dois extremos do trecho em estudo, reduzindo o
volume que antes derrubava a API.

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
CLASSES = "motorway|trunk|primary|secondary|tertiary|unclassified|road|track"
MARGEM_M = 3000.0
DESTINO = Path("data/processed/rede_completa.geojson")

oeste, sul, leste, norte = extensao_com_margem([BAMBUI, ESTEIOS], MARGEM_M)
print(f"Caixa: sul {sul:.4f}, oeste {oeste:.4f}, norte {norte:.4f}, leste {leste:.4f}")

consulta = f"""
[out:json][timeout:180];
way["highway"~"^({CLASSES})$"]({sul},{oeste},{norte},{leste});
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
    print(f"HTTP {erro.code} — resposta do servidor:\n")
    print(erro.read().decode("utf-8", errors="replace")[:2000])
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

DESTINO.parent.mkdir(parents=True, exist_ok=True)
DESTINO.write_text(json.dumps({"type": "FeatureCollection", "features": feicoes}))

print(f"Vértices no total: {total_vertices:,}")
print(f"Gravado: {DESTINO} ({DESTINO.stat().st_size / 1024**2:.1f} MB)")

por_superficie = defaultdict(int)
por_classe = defaultdict(int)
for feicao in feicoes:
    por_superficie[feicao["properties"].get("surface", "(sem tag)")] += 1
    por_classe[feicao["properties"].get("highway", "?")] += 1

print("\nPor revestimento:")
for chave, valor in sorted(por_superficie.items(), key=lambda i: -i[1]):
    print(f"  {chave:<15} {valor:>4}")

print("\nPor classe:")
for chave, valor in sorted(por_classe.items(), key=lambda i: -i[1]):
    print(f"  {chave:<15} {valor:>4}")
