"""Compara a alternativa gerada com o traçado existente.

As métricas são independentes da função de custo que gerou a alternativa:
comparar pela grandeza que uma delas foi otimizada para minimizar seria
circular.

A classe de rodovia adotada é premissa do estudo, com procedência e estado
de verificação declarados em config/estudo.py.

Dados do OpenStreetMap (ODbL) e de elevação Copernicus DEM.
"""

import json
from itertools import pairwise
from pathlib import Path

import networkx as nx
from pyproj import Geod

from bambui_luz.config.estudo import (
    BAMBUI,
    CLASSE_ADOTADA,
    CRS_GEOGRAFICO,
    CRS_TRABALHO,
    ESTEIOS,
)
from bambui_luz.domain.geometria import Ponto, Tracado
from bambui_luz.infrastructure.coordenadas import criar_transformador
from bambui_luz.infrastructure.mde import ProvedorElevacaoRaster
from bambui_luz.services.comparar_alternativas import resumir
from bambui_luz.services.extrair_perfil import extrair_perfil

MDE = Path("data/processed/mde_corredor.tif")
REDE = Path("data/processed/rede_completa.geojson")
ALTERNATIVA = Path("data/processed/alternativa_menor_custo.geojson")
DESTINO = Path("data/processed/comparacao.json")
CASAS_DECIMAIS = 5


geodesico = Geod(ellps="GRS80")
para_metros = criar_transformador(CRS_GEOGRAFICO, CRS_TRABALHO)


def em_tracado(coordenadas) -> Tracado:
    """Converte coordenadas geográficas em traçado métrico."""
    pontos = []
    for longitude, latitude in coordenadas:
        x, y = para_metros.transform(longitude, latitude)
        pontos.append(Ponto(x=x, y=y))
    return Tracado(pontos=tuple(pontos))


def montar_grafico(colecao) -> nx.MultiGraph:
    """Monta o grafo viário vértice a vértice a partir do GeoJSON."""
    grafo = nx.MultiGraph()
    for feicao in colecao["features"]:
        for anterior, atual in pairwise(feicao["geometry"]["coordinates"]):
            _, _, extensao = geodesico.inv(anterior[0], anterior[1], atual[0], atual[1])
            grafo.add_edge(
                (
                    round(anterior[0], CASAS_DECIMAIS),
                    round(anterior[1], CASAS_DECIMAIS),
                ),
                (round(atual[0], CASAS_DECIMAIS), round(atual[1], CASAS_DECIMAIS)),
                extensao_m=extensao,
            )
    return grafo


def mais_proximo(grafo, longitude, latitude):
    """Encontra o vértice do grafo mais próximo de uma coordenada."""
    melhor, menor = None, float("inf")
    for no in grafo.nodes:
        _, _, distancia = geodesico.inv(longitude, latitude, no[0], no[1])
        if distancia < menor:
            melhor, menor = no, distancia
    return melhor


grafo = montar_grafico(json.loads(REDE.read_text(encoding="utf-8")))
existente = nx.shortest_path(
    grafo,
    mais_proximo(grafo, BAMBUI.longitude_graus, BAMBUI.latitude_graus),
    mais_proximo(grafo, ESTEIOS.longitude_graus, ESTEIOS.latitude_graus),
    weight="extensao_m",
)

alternativa = json.loads(ALTERNATIVA.read_text(encoding="utf-8"))
coordenadas_alternativa = [
    tuple(c) for c in alternativa["features"][0]["geometry"]["coordinates"]
]

tracados = {
    "Existente (OSM)": em_tracado(existente),
    "Menor custo": em_tracado(coordenadas_alternativa),
}

resumos = []
with ProvedorElevacaoRaster(MDE) as provedor:
    for nome, tracado in tracados.items():
        perfil = extrair_perfil(tracado, provedor)
        resumos.append(resumir(nome, perfil, CLASSE_ADOTADA))

print(f"Classe adotada: {CLASSE_ADOTADA.nome}")
print(f"Rampa máxima: {CLASSE_ADOTADA.rampa_maxima_pct:.1f}%")
print(f"Velocidade diretriz: {CLASSE_ADOTADA.velocidade_diretriz_kmh:.0f} km/h\n")

cabecalho = (
    f"{'Alternativa':<18}{'Ext (km)':>10}{'Subida':>9}{'Descida':>9}"
    f"{'Relevo':>9}{'Rampa máx':>11}{'Inadm (km)':>12}"
)

print(cabecalho)
print("-" * len(cabecalho))
for r in resumos:
    print(
        f"{r.nome:<18}{r.extensao_km:>10.2f}{r.subida_acumulada_m:>9.0f}"
        f"{r.descida_acumulada_m:>9.0f}{r.relevo_vencido_m:>9.0f}"
        f"{r.rampa_maxima_pct:>10.2f}%{r.extensao_inadmissivel_km:>12.2f}"
    )

base, nova = resumos
print("\nVariação da alternativa em relação ao existente:")
for rotulo, antes, depois in (
    ("extensão (km)", base.extensao_km, nova.extensao_km),
    ("relevo vencido (m)", base.relevo_vencido_m, nova.relevo_vencido_m),
    ("rampa máxima (%)", base.rampa_maxima_pct, nova.rampa_maxima_pct),
    (
        "extensão inadmissível (km)",
        base.extensao_inadmissivel_km,
        nova.extensao_inadmissivel_km,
    ),
):
    if antes == 0:
        print(f"   {rotulo}: {depois:.2f} (base zero)")
        continue
    variacao = 100 * (depois - antes) / antes
    print(f"    {rotulo}: {antes:.2f} -> {depois:.2f}  ({variacao:+.1f}%)")

DESTINO.write_text(
    json.dumps(
        {
            "classe_adotada": {
                "nome": CLASSE_ADOTADA.nome,
                "rampa_maxima_pct": CLASSE_ADOTADA.rampa_maxima_pct,
                "velocidade_diretriz_km": CLASSE_ADOTADA.velocidade_diretriz_kmh,
                "fonte": CLASSE_ADOTADA.fonte,
            },
            "alternativas": [
                {
                    "nome": r.nome,
                    "extensao_km": r.extensao_km,
                    "subida_acumulada_m": r.subida_acumulada_m,
                    "descida_acumulada_m": r.descida_acumulada_m,
                    "desnivel_liquido_m": r.desnivel_liquido_m,
                    "rampa_maxima_pct": r.rampa_maxima_pct,
                    "extensao_inadmissivel_km": r.extensao_inadmissivel_km,
                    "estacoes": r.estacoes,
                }
                for r in resumos
            ],
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(f"\nGravado: {DESTINO}")
