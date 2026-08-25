"""Verificação da disponibilidade dos tiles de elevação.

Consulta o servidor sem transferir o conteúdo, para confirmar a convenção
de nomes antes de iniciar downloads.
"""

import urllib.error
import urllib.request

from bambui_luz.config.estudo import BAMBUI, ESTEIOS, LUZ
from bambui_luz.infrastructure.aquisicao import tiles_necessarios, url_tile

coordenadas = [
    (local.latitude_graus, local.longitude_graus) for local in (BAMBUI, ESTEIOS, LUZ)
]

for nome in tiles_necessarios(coordenadas):
    url = url_tile(nome)
    requisicao = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            tamanho_mb = int(resposta.headers.get("Content-Length", 0)) / 1024**2
            print(f"OK   {nome}  ({tamanho_mb:.1f} MB)")
    except urllib.error.HTTPError as erro:
        print(f"FALHA {nome}  HTTP {erro.code}")
    except urllib.error.URLError as erro:
        print(f"ERRO   {nome} {erro.reason}")
