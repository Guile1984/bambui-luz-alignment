"""Gera os diagramas de massa das alternativas de traçado.

Dados do OpenStreetMap (ODbL) e de elevação Copernicus DEM.
"""

import json
from pathlib import Path

from bambui_luz.config.estudo import (
    BAMBUI,
    CRS_GEOGRAFICO,
    CRS_TRABALHO,
    ESTEIOS,
    FATOR_CONVERSAO_CORTE_ATERRO,
    JANELA_SUAVIZACAO_GREIDE_M,
    LARGURA_PLATAFORMA_M,
    TALUDE_ATERRO_H_V,
    TALUDE_CORTE_H_V,
)
from bambui_luz.domain.geometria import Ponto, Tracado
from bambui_luz.domain.greide import suavizar
from bambui_luz.domain.terraplenagem import (
    SecaoTransversal,
    alturas_de_trabalho,
    curva_de_massa,
)
from bambui_luz.infrastructure.coordenadas import criar_transformador
from bambui_luz.infrastructure.malha_viaria import (
    caminho_mais_curto,
    montar_grafo,
    vertice_mais_proximo,
)
from bambui_luz.infrastructure.mde import ProvedorElevacaoRaster
from bambui_luz.presentation.grafico_massa import desenhar_massa
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
    "existente": (
        "Traçado existente - Bambuí a Esteios",
        em_tracado(existente),
    ),
    "menor_custo": (
        "Alternativa por menor custo - Bambuí a Esteios",
        em_tracado(
            [tuple(c) for c in alternativa["features"][0]["geometry"]["coordinates"]]
        ),
    ),
}

with ProvedorElevacaoRaster(MDE) as provedor:
    for chave, (titulo, tracado) in tracados.items():
        perfil = extrair_perfil(tracado, provedor)
        greide = suavizar(perfil, JANELA_SUAVIZACAO_GREIDE_M)
        alturas = alturas_de_trabalho(perfil, greide)
        ordenadas = curva_de_massa(perfil, greide, SECAO, FATOR_CONVERSAO_CORTE_ATERRO)
        caminho = desenhar_massa(
            perfil,
            greide,
            alturas,
            ordenadas,
            Path(f"data/processed/massa_{chave}.png"),
            titulo,
        )
        print(f"Gravado: {caminho}")
