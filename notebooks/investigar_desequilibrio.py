"""Investiga o desequilíbrio entre corte e aterro na curva de massa.

Duas hipóteses: o greide por média móvel pode ficar sistematicamente
acima do terreno em relevo assimétrico (H1), ou a diferença de talude
entre corte e aterro pode gerar mais volume de aterro para alturas
equilibradas (H2).

Dados do OpenStreetMap (ODbL) e de elevação Copernicus DEM.
"""

import json
from pathlib import Path

import numpy as np

from bambui_luz.config.estudo import (
    BAMBUI,
    CLASSE_ADOTADA,
    CRS_GEOGRAFICO,
    CRS_TRABALHO,
    ESTEIOS,
    JANELA_SUAVIZACAO_GREIDE_M,
    LARGURA_PLATAFORMA_M,
    TALUDE_ATERRO_H_V,
    TALUDE_CORTE_H_V,
)
from bambui_luz.domain.geometria import Ponto, Tracado
from bambui_luz.domain.greide import suavizar
from bambui_luz.domain.terraplenagem import SecaoTransversal, alturas_de_trabalho
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

SECAO = SecaoTransversal(
    largura_plataforma_m=LARGURA_PLATAFORMA_M,
    talude_corte_h_v=TALUDE_CORTE_H_V,
    talude_aterro_h_v=TALUDE_ATERRO_H_V,
)
para_metros = criar_transformador(CRS_GEOGRAFICO, CRS_TRABALHO)


def em_tracado(coordenadas) -> Tracado:
    """Converte coordenadas geográficas em traçado métrico."""
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
        [tuple(c) for c in alternativa["features"][0]["geometry"]["coordinates"]]
    ),
}

print("H1 — o greide fica acima do terreno?\n")
with ProvedorElevacaoRaster(MDE) as provedor:
    for nome, tracado in tracados.items():
        perfil = extrair_perfil(tracado, provedor)
        greide = suavizar(perfil, JANELA_SUAVIZACAO_GREIDE_M)
        alturas = np.array(alturas_de_trabalho(perfil, greide))
        aterros = alturas[alturas > 0]
        cortes = -alturas[alturas < 0]

        print(f"  {nome}:")
        print(f"    altura média (positiva = aterro): {alturas.mean():+.3f} m")
        print(
            f"    estações em aterro: {len(aterros)} "
            f"({100 * len(aterros) / len(alturas):.1f}%)"
        )
        print(
            f"    estações em corte:  {len(cortes)} "
            f"({100 * len(cortes) / len(alturas):.1f}%)"
        )
        print(f"    altura média de aterro: {aterros.mean():.2f} m")
        print(f"    altura média de corte:  {cortes.mean():.2f} m")
        print(f"    soma das alturas de aterro: {aterros.sum():.0f} m")
        print(f"    soma das alturas de corte:  {cortes.sum():.0f} m")

print("\nH2 — quanto do desequilíbrio vem da assimetria dos taludes?\n")
for altura in (2.0, 5.0, 10.0, 20.0):
    corte = SECAO.area_corte(altura)
    aterro = SECAO.area_aterro(altura)
    print(
        f"  altura {altura:>4.0f} m: corte {corte:>7.1f} m2, "
        f"aterro {aterro:>7.1f} m2  (aterro {100 * (aterro / corte - 1):+.1f}%)"
    )

print("\nConflito entre compensação e conformidade:\n")
cabecalho = (
    f"{'Janela (m)':>11}{'Rampa máx':>11}{'Inadm':>8}"
    f"{'Corte (m3)':>14}{'Aterro (m3)':>14}{'Saldo (m3)':>14}{'m3/km':>10}"
)
print(cabecalho)
print("-" * len(cabecalho))

with ProvedorElevacaoRaster(MDE) as provedor:
    for nome, tracado in tracados.items():
        print(f"\n{nome}:")
        perfil = extrair_perfil(tracado, provedor)
        extensao_km = perfil.extensao / 1000
        distancias = np.diff([e.distancia_m for e in perfil.estacoes])
        for janela in (300.0, 500.0, 800.0, 1000.0, 1500.0, 2000.0, 3000.0):
            greide = suavizar(perfil, janela)
            alturas = np.array(alturas_de_trabalho(perfil, greide))
            areas_corte = np.array([SECAO.area_corte(-a) for a in alturas])
            areas_aterro = np.array([SECAO.area_aterro(a) for a in alturas])
            corte = float(((areas_corte[:-1] + areas_corte[1:]) / 2 * distancias).sum())
            aterro = float(
                ((areas_aterro[:-1] + areas_aterro[1:]) / 2 * distancias).sum()
            )
            inadmissiveis = len(greide.segmentos_inadmissiveis(CLASSE_ADOTADA))
            movimentado = corte + aterro
            print(
                f"{janela:>11.0f}{greide.rampa_maxima_absoluta:>10.2f}%"
                f"{inadmissiveis:>8}{corte:>14,.0f}{aterro:>14,.0f}"
                f"{corte * 0.9 - aterro:>14,.0f}"
                f"{movimentado / extensao_km:>10,.0f}"
            )
