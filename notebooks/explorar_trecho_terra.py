"""Busca as vias mapeadas entre Bambuí e Esteios, com ou sem designação.

A consulta anterior filtrou por presença da tag ref e não alcançou vias
sem designação oficial, categoria em que costumam estar as estradas
rurais não pavimentadas.

Dados do OpenStreetMap, disponibilizados sob ODbL.
"""

import json
import urllib.parse
import urllib.request
from collections import defaultdict

from bambui_luz.config.estudo import BAMBUI, ESTEIOS
from bambui_luz.infrastructure.mosaico import extensao_com_margem

OVERPASS = "https://overpass-api.de/api/interpreter"
IDENTIFICACAO = (
    "bambui-luz-alignment/0.1 (https://github.com/Guile1984/bambui-luz-alignment)"
)
CLASSES_RURAIS = "primary|secondary|tertiary|unclassified|track|road"

oeste, sul, leste, norte = extensao_com_margem([BAMBUI, ESTEIOS], 2000.0)
print(f"Caixa: sul {sul:.4f}, oeste {oeste:.4f}, norte {norte:.4f}, leste {leste:.4f}")

consulta = f"""
[out:json][timeout:120];
way["highway"~"^({CLASSES_RURAIS})$"]({sul},{oeste},{norte},{leste});
out tags;
"""

dados = urllib.parse.urlencode({"data": consulta}).encode("utf-8")
requisicao = urllib.request.Request(
    OVERPASS, data=dados, headers={"User-Agent": IDENTIFICACAO}
)

with urllib.request.urlopen(requisicao, timeout=180) as resposta:
    resultado = json.load(resposta)

elementos = resultado["elements"]
print(f"\nTrechos encontrados: {len(elementos)}")

por_superficie = defaultdict(int)
for elemento in elementos:
    por_superficie[elemento.get("tags", {}).get("surface", "(sem tag)")] += 1

print("\nDistribuição por revestimento:")
for superficie, quantidade in sorted(por_superficie.items(), key=lambda item: -item[1]):
    print(f"  {superficie:<20} {quantidade:>4}")

print("\nVias nomeadas ou designadas, com 3 ou mais trechos:")
por_via = defaultdict(list)
for elemento in elementos:
    tags = elemento.get("tags", {})
    chave = tags.get("ref") or tags.get("name")
    if chave:
        por_via[chave].append(tags)

for via in sorted(por_via):
    trechos = por_via[via]
    if len(trechos) < 3:
        continue
    classes = sorted({t.get("highway", "?") for t in trechos})
    superficies = sorted({t.get("surface", "(sem tag)") for t in trechos})
    print(
        f"  {via}: {len(trechos)} trechos | {', '.join(classes)} | "
        f"{', '.join(superficies)}"
    )
