"""Extração do perfil longitudinal do traçado real Bambuí-Esteios.

Reúne o caminho mínimo obtido do grafo viário, o modelo de elevação
aferido e o serviço de extração. Primeiro perfil real do estudo.

Dados do OpenStreetMap, disponibilizados sob ODbL.
Dados de elevação Copernicus DEM.
"""

import json
from itertools import pairwise
from pathlib import Path

import networkx as nx
from pyproj import Geod

from bambui_luz.config.estudo import BAMBUI, CRS_GEOGRAFICO, CRS_TRABALHO, ESTEIOS
from bambui_luz.domain.geometria import Ponto, Tracado
from bambui_luz.infrastructure.coordenadas import criar_transformador
from bambui_luz.infrastructure.mde import ProvedorElevacaoRaster
from bambui_luz.services.extrair_perfil import extrair_perfil

REDE = Path("data/processed/rede_completa.geojson")
MDE = Path("data/processed/mde_corredor.tif")
DESTINO = Path("data/processed/perfil_bambui_esteios.json")
CASAS_DECIMAIS = 5

geodesico = Geod(ellps="GRS80")
colecao = json.loads(REDE.read_text(encoding="utf-8"))


def vertice(coordenada):
    return (round(coordenada[0], CASAS_DECIMAIS), round(coordenada[1], CASAS_DECIMAIS))


grafo = nx.MultiGraph()
for feicao in colecao["features"]:
    coordenadas = feicao["geometry"]["coordinates"]
    superficie = feicao["properties"].get("surface", "(sem tag)")
    for anterior, atual in pairwise(coordenadas):
        _, _, extensao = geodesico.inv(anterior[0], anterior[1], atual[0], atual[1])
        grafo.add_edge(
            vertice(anterior),
            vertice(atual),
            extensao_m=extensao,
            superficie=superficie,
        )


def vertice_mais_proximo(longitude, latitude):
    melhor, menor = None, float("inf")
    for no in grafo.nodes:
        _, _, distancia = geodesico.inv(longitude, latitude, no[0], no[1])
        if distancia < menor:
            melhor, menor = no, distancia
    return melhor


origem = vertice_mais_proximo(BAMBUI.longitude_graus, BAMBUI.latitude_graus)
destino = vertice_mais_proximo(ESTEIOS.longitude_graus, ESTEIOS.latitude_graus)
caminho = nx.shortest_path(grafo, origem, destino, weight="extensao_m")
print(f"Caminho: {len(caminho)} vértices")

para_metros = criar_transformador(CRS_GEOGRAFICO, CRS_TRABALHO)
pontos = []
for longitude, latitude in caminho:
    x, y = para_metros.transform(longitude, latitude)
    pontos.append(Ponto(x=x, y=y))

tracado = Tracado(pontos=tuple(pontos))
print(f"Extensão do traçado: {tracado.extensao / 1000:.2f} km")

with ProvedorElevacaoRaster(MDE) as provedor:
    perfil = extrair_perfil(tracado, provedor)

print(f"\nEstações no perfil: {len(perfil):,}")
print(f"Extensão: {perfil.extensao / 1000:.2f} km")
print(f"Desnível entre extremos: {perfil.desnivel:+.1f} m")

cotas = [e.cota_m for e in perfil.estacoes]
print(f"Cota mínima: {min(cotas):.1f} m")
print(f"Cota máxima: {max(cotas):.1f} m")
print(f"Amplitude: {max(cotas) - min(cotas):.1f} m")

rampas = perfil.rampas()
subida = sum(
    b.cota_m - a.cota_m for a, b in pairwise(perfil.estacoes) if b.cota_m > a.cota_m
)
descida = sum(
    a.cota_m - b.cota_m for a, b in pairwise(perfil.estacoes) if b.cota_m < a.cota_m
)
print(f"\nSubida acumulada: {subida:.0f} m")
print(f"Descida acumulada: {descida:.0f} m")
print(f"Rampa máxima absoluta: {perfil.rampa_maxima_absoluta:.2f}%")

for limite in (3.0, 5.0, 6.0, 8.0):
    excedentes = sum(1 for r in rampas if abs(r) > limite)
    metros = excedentes * 20.0
    pct = 100 * excedentes / len(rampas)
    print(
        f"  segmentos acima de {limite:.0f}%: {excedentes:>4} "
        f"({metros / 1000:.2f} km, {pct:.1f}%)"
    )

DESTINO.write_text(
    json.dumps(
        [{"distancia_m": e.distancia_m, "cota_m": e.cota_m} for e in perfil.estacoes]
    ),
    encoding="utf-8",
)
print(f"\nPerfil gravado: {DESTINO}")
print("\nSensibilidade ao passo de amostragem:")
print(f"{'passo':>8}{'estações':>10}{'rampa máx':>12}{'>8%':>10}{'>5%':>10}")
with ProvedorElevacaoRaster(MDE) as provedor:
    for passo in (20.0, 30.0, 60.0, 100.0, 200.0):
        p = extrair_perfil(tracado, provedor, passo_m=passo)
        r = p.rampas()
        acima_8 = 100 * sum(1 for x in r if abs(x) > 8) / len(r)
        acima_5 = 100 * sum(1 for x in r if abs(x) > 5) / len(r)
        print(
            f"{passo:>8.0f}{len(p):>10,}{p.rampa_maxima_absoluta:>11.2f}%"
            f"{acima_8:>9.1f}%{acima_5:>9.1f}%"
        )
