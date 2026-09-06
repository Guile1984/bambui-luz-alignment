"""Calcula os volumes de terraplenagem das alternativas de traçado.

Os volumes decorrem de um greide simplificado por suavização e de seção
transversal sobre terreno transversalmente horizontal. Prestam-se à
comparação relativa entre alternativas, não ao dimensionamento da obra.

Dados do OpenStreetMap (ODbL) e de elevação Copernicus DEM.
"""

import json
from pathlib import Path

from bambui_luz.config.estudo import (
    BAMBUI,
    CLASSE_ADOTADA,
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
    calcular_volumes,
    curva_de_massa,
)
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
DESTINO = Path("data/processed/terraplenagem.json")

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
coordenadas_alternativa = [
    tuple(c) for c in alternativa["features"][0]["geometry"]["coordinates"]
]

tracados = {
    "Existente (OSM)": em_tracado(existente),
    "Menor custo": em_tracado(coordenadas_alternativa),
}

print(
    f"Seção: plataforma {LARGURA_PLATAFORMA_M:.1f} m, "
    f"talude corte {TALUDE_CORTE_H_V:.1f}:1, "
    f"aterro {TALUDE_ATERRO_H_V:.1f}:1"
)
print(f"Janela de suavização do greide: {JANELA_SUAVIZACAO_GREIDE_M:.0f} m")
print(f"Fator de conversão corte-aterro: {FATOR_CONVERSAO_CORTE_ATERRO:.2f}\n")

resultados = []
with ProvedorElevacaoRaster(MDE) as provedor:
    for nome, tracado in tracados.items():
        perfil = extrair_perfil(tracado, provedor)
        greide = suavizar(perfil, JANELA_SUAVIZACAO_GREIDE_M)
        volumes = calcular_volumes(perfil, greide, SECAO, FATOR_CONVERSAO_CORTE_ATERRO)
        ordenadas = curva_de_massa(perfil, greide, SECAO, FATOR_CONVERSAO_CORTE_ATERRO)
        inadmissiveis = greide.segmentos_inadmissiveis(CLASSE_ADOTADA)
        resultados.append(
            {
                "nome": nome,
                "extensao_km": perfil.extensao / 1000,
                "corte_m3": volumes.corte_m3,
                "aterro_m3": volumes.aterro_m3,
                "movimentado_m3": volumes.movimentado_m3,
                "saldo_m3": volumes.saldo_m3,
                "compensado": volumes.compensado,
                "rampa_maxima_greide_pct": greide.rampa_maxima_absoluta,
                "segmentos_inadmissiveis": len(inadmissiveis),
                "segmentos_totais": len(greide.rampas()),
                "curva_maxima_m3": max(ordenadas),
                "curva_minima_m3": min(ordenadas),
                "ordenadas": ordenadas,
            }
        )

cabecalho = (
    f"{'Alternativa':<18}{'Ext (km)':>10}{'Corte':>12}{'Aterro':>12}"
    f"{'Movim.':>12}{'Saldo':>12}{'m3/km':>10}"
)
print(cabecalho)
print("-" * len(cabecalho))
for r in resultados:
    print(
        f"{r['nome']:<18}{r['extensao_km']:>10.2f}{r['corte_m3']:>12,.0f}"
        f"{r['aterro_m3']:>12,.0f}{r['movimentado_m3']:>12,.0f}"
        f"{r['saldo_m3']:>12,.0f}"
        f"{r['movimentado_m3'] / r['extensao_km']:>10,.0f}"
    )

print("\nGreide e compensação:")
for r in resultados:
    situacao = "compensado" if r["compensado"] else "não compensado"
    print(f"  {r['nome']}:")
    print(f"    rampa máxima do greide: {r['rampa_maxima_greide_pct']:.2f}%")
    print(
        f"    segmentos acima da classe: {r['segmentos_inadmissiveis']} "
        f"de {r['segmentos_totais']}"
    )
    print(f"    curva de massa: {situacao}")
    print(
        f"    ordenada máxima {r['curva_maxima_m3']:,.0f} m3, "
        f"mínima {r['curva_minima_m3']:,.0f} m3"
    )

base, nova = resultados
print("\nVariação da alternativa em relação ao existente:")
for rotulo, chave in (
    ("volume movimentado (m3)", "movimentado_m3"),
    ("corte (m3)", "corte_m3"),
    ("aterro (m3)", "aterro_m3"),
):
    variacao = 100 * (nova[chave] - base[chave]) / base[chave]
    print(f"  {rotulo}: {base[chave]:,.0f} -> {nova[chave]:,.0f}  ({variacao:+.1f}%)")

DESTINO.write_text(
    json.dumps(
        {
            "premissas": {
                "largura_plataforma_m": LARGURA_PLATAFORMA_M,
                "talude_corte_h_v": TALUDE_CORTE_H_V,
                "talude_aterro_h_v": TALUDE_ATERRO_H_V,
                "fator_conversao": FATOR_CONVERSAO_CORTE_ATERRO,
                "janela_suavizacao_m": JANELA_SUAVIZACAO_GREIDE_M,
                "classe": CLASSE_ADOTADA.nome,
            },
            "alternativas": resultados,
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(f"\nGravado: {DESTINO}")

print("\nDistribuição das alturas de trabalho:")
with ProvedorElevacaoRaster(MDE) as provedor:
    for nome, tracado in tracados.items():
        perfil = extrair_perfil(tracado, provedor)
        greide = suavizar(perfil, JANELA_SUAVIZACAO_GREIDE_M)
        alturas = alturas_de_trabalho(perfil, greide)
        aterros = [a for a in alturas if a > 0]
        cortes = [-a for a in alturas if a < 0]
        print(f"  {nome}:")
        print(f"    maior aterro: {max(aterros, default=0):.1f} m")
        print(f"    maior corte: {max(cortes, default=0):.1f} m")
        print(
            f"    estações com aterro acima de 10 m: "
            f"{sum(1 for a in aterros if a > 10)}"
        )
        print(
            f"    estações com aterro acima de 20 m: "
            f"{sum(1 for a in aterros if a > 20)}"
        )
