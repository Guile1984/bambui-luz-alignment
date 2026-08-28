"""Exploração das rodovias com designação oficial no corredor de estudo.

Consulta a API Overpass para descobrir quais rodovias estão mapeadas na
região, com que designação e com que atributo de revestimento. Script
exploratório: depende de rede e não integra a suíte de testes.

Dados do OpenStreetMap, disponibilizados sob ODbL.
"""

import json
import urllib.parse
import urllib.request
from collections import defaultdict

from bambui_luz.config.estudo import BAMBUI, ESTEIOS, LUZ, MARGEM_CORREDOR_M
from bambui_luz.infrastructure.mosaico import extensao_com_margem

OVERPASS = "https://overpass-api.de/api/interpreter"

IDENTIFICACAO = (
    "bambui-luz-alignment/0.1 (https://github.com/Guile1984/bambui-luz-alignment)"
)
"""Identificação do cliente, conforme etiqueta de uso da API Overpass."""

oeste, sul, leste, norte = extensao_com_margem(
    [BAMBUI, ESTEIOS, LUZ], MARGEM_CORREDOR_M
)
print(
    f"Caixa consultada: sul {sul:.4f}, oeste {oeste:.4f}, "
    f"norte {norte:.4f}, leste {leste:.4f}"
)

consulta = f"""
[out:json][timeout:90];
way["highway"]["ref"]({sul},{oeste},{norte},{leste});
out tags;
"""

dados = urllib.parse.urlencode({"data": consulta}).encode("utf-8")
requisicao = urllib.request.Request(
    OVERPASS,
    data=dados,
    headers={"User-Agent": IDENTIFICACAO},
)
with urllib.request.urlopen(requisicao, timeout=120) as resposta:
    resultado = json.load(resposta)

elementos = resultado["elements"]
print(f"\nTrechos com designação encontradas: {len(elementos)}\n")

por_designacao = defaultdict(list)
for elemento in elementos:
    tags = elemento.get("tags", {})
    por_designacao[tags.get("ref", "(sem ref)")].append(tags)

for designacao in sorted(por_designacao):
    trechos = por_designacao[designacao]
    classes = sorted({t.get("highway", "?") for t in trechos})
    superficies = sorted({t.get("surface", "(sem tag surface)") for t in trechos})
    print(f"{designacao}: {len(trechos)} trechos")
    print(f"  classes: {', '.join(classes)}")
    print(f"  superfícies: {', '.join(superficies)}")
