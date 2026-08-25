"""Consulta a listagem pública do bucket para descobrir os nomes reais.

Diagnóstico: a montagem da URL de download resultou em HTTP 404. A API de
listagem do S3 informa quais chaves existem sob um dado prefixo.
"""

import urllib.request

BUCKET = "https://copernicus-dem-30m.s3.amazonaws.com"
PREFIXOS = [
    "Copernicus_DSM_COG_10_S21_00_W046",
    "Copernicus_DSM_COG_10_S20_00_W046",
]

for prefixo in PREFIXOS:
    url = f"{BUCKET}/?list-type=2&prefix={prefixo}&max-keys=10"
    print(f"\n=== {prefixo} ===")
    with urllib.request.urlopen(url, timeout=30) as resposta:
        conteudo = resposta.read().decode("utf-8")
    for linha in conteudo.split("<Key>")[1:]:
        print("  " + linha.split("</Key>")[0])
    if "<Key>" not in conteudo:
        print("  (nenhuma chave encontrada sob este prefixo)")
