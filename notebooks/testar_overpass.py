"""Distingue indisponibilidade do serviço Overpass de consulta pesada demais.

Consulta uma caixa mínima em torno de Bambuí, pedindo geometria. Se esta
consulta funcionar, o serviço está no ar e o problema é o volume pedido.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

IDENTIFICACAO = (
    "bambui-luz-alignment/0.1 (https://github.com/Guile1984/bambui-luz-alignment)"
)
INSTANCIAS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

consulta = """
[out:json][timeout:60];
way["highway"](-20.02,-45.99,-20.00,-45.97);
out geom;
"""

for instancia in INSTANCIAS:
    print(f"\n=== {instancia} ===")
    dados = urllib.parse.urlencode({"data": consulta}).encode("utf-8")
    requisicao = urllib.request.Request(
        instancia, data=dados, headers={"User-Agent": IDENTIFICACAO}
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=90) as resposta:
            resultado = json.load(resposta)
        elementos = resultado["elements"]
        vertices = sum(len(e.get("geometry", [])) for e in elementos)
        print(f"OK — {len(elementos)} trechos, {vertices} vértices")
    except urllib.error.HTTPError as erro:
        print(f"HTTP {erro.code}")
        corpo = erro.read().decode("utf-8", errors="replace")[:500]
        if corpo.strip():
            print(f"  {corpo}")
    except urllib.error.URLError as erro:
        print(f"Sem resposta: {erro.reason}")
