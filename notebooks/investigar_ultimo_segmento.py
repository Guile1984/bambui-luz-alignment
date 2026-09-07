"""Verifica se o último segmento do perfil é um toco que distorce as rampas.

Hipótese: o estaqueamento acrescenta a extensão total como última estação,
de modo que o segmento final pode ter comprimento arbitrariamente pequeno.
Rampa calculada sobre denominador minúsculo resulta em valor espúrio.

Dados do OpenStreetMap (ODbL) e de elevação Copernicus DEM.
"""

import json
from pathlib import Path

import numpy as np

from bambui_luz.config.estudo import (
    BAMBUI,
    CRS_GEOGRAFICO,
    CRS_TRABALHO,
    ESTEIOS,
)
from bambui_luz.domain.geometria import Ponto, Tracado
from bambui_luz.domain.greide import suavizar
from bambui_luz.infrastructure.coordenadas import criar_transformador
from bambui_luz.infrastructure.malha_viaria import (
    caminho_mais_curto,
    montar_grafo,
    vertice_mais_proximo,
)
from bambui_luz.infrastructure.mde import ProvedorElevacaoRaster
from bambui_luz.services.extrair_perfil import extrair_perfil

MDE = Path("data/processed/mde_corredor.tif")
REDE = Path("data/processed/rede_completa.geojson")
ALTERNATIVA = Path("data/processed/alternativa_menor_custo.geojson")

para_metros = criar_transformador(CRS_GEOGRAFICO, CRS_TRABALHO)


def em_tracado(coordenadas) -> Tracado:
    """Converte coordenadas geográficas em traçdo métrico."""
    pontos = []
    for longitude, latitude in coordenadas:
        x, y = para_metros.transform(longitude, latitude)
        pontos.append(Ponto(x=x, y=y))
    return Tracado(pontos=tuple(pontos))


grafo = montar_grafo(json.loads(REDE.read_text(encoding="utf-8")))
existente = caminho_mais_curto(
    grafo,
    vertice_mais_proximo(grafo, BAMBUI.longitude_graus, BAMBUI.latitude_graus),
    vertice_mais_proximo(grafo, ESTEIOS.longitude_graus, ESTEIOS.latitude_graus),
)
alternativa = json.loads(ALTERNATIVA.read_text(encoding="utf-8"))

tracados = {
    "Existente (OSM)": em_tracado(existente),
    "Menor custo": em_tracado(
        [tuple(c) for c in alternativa["features"][0]["geometry"]["coordinates"]],
    ),
}

with ProvedorElevacaoRaster(MDE) as provedor:
    for nome, tracado in tracados.items():
        perfil = extrair_perfil(tracado, provedor)
        distancias = np.array([e.distancia_m for e in perfil.estacoes])
        comprimentos = np.diff(distancias)

        print(f"\n=== {nome} ===")
        print(f"  extensão: {perfil.extensao:.3f} m")
        print(f"  estações: {len(perfil)}")
        print(f"  comprimento do último segmento: {comprimentos[-1]:.3f} m")
        print(
            f"  menor segmento: {comprimentos.min():.3f} m "
            f"(índice {int(comprimentos.argmin())})"
        )

        rampas_terreno = np.array(perfil.rampas())
        indice = int(np.abs(rampas_terreno).argmax())
        print(
            f"  rampa máxima do terreno: {np.abs(rampas_terreno).max():.2f}% "
            f"no segmento {indice} (comprimento {comprimentos[indice]:.1f} m)"
        )

        rampas_sem_ultimo = np.abs(rampas_terreno[:-1])
        print(
            f"  rampa máxima ignorando o último segmento: "
            f"{rampas_sem_ultimo.max():.2f}%"
        )

        for janela in (1500.0, 3000.0):
            greide = suavizar(perfil, janela)
            rampas = np.abs(np.array(greide.rampas()))
            indice = int(rampas.argmax())
            print(
                f"  greide janela {janela:.0f} m: máxima {rampas.max():.2f}% "
                f"no segmento {indice} (comprimento {comprimentos[indice]:.1f} m); "
                f"sem o último: {rampas[:-1].max():.2f}%"
            )
