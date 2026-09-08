"""Gera o relatório consolidado do estudo.

Reúne as métricas das alternativas e as premissas adotadas em arquivo
único, fonte dos números apresentados no README.

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
from bambui_luz.domain.terraplenagem import SecaoTransversal
from bambui_luz.infrastructure.coordenadas import criar_transformador
from bambui_luz.infrastructure.malha_viaria import (
    caminho_mais_curto,
    montar_grafo,
    vertice_mais_proximo,
)
from bambui_luz.infrastructure.mde import ProvedorElevacaoRaster
from bambui_luz.services.extrair_perfil import PASSO_ESTACA_M, extrair_perfil
from bambui_luz.services.relatorio import Premissas, Relatorio, compor_linha

MDE = Path("data/processed/mde_corredor.tif")
REDE = Path("data/processed/rede_completa.geojson")
ALTERNATIVA = Path("data/processed/alternativa_menor_custo.geojson")
DESTINO = Path("data/processed/relatorio.json")
RESOLUCAO_MDE_M = 30.0

PREMISSAS = Premissas(
    classe=CLASSE_ADOTADA,
    secao=SecaoTransversal(
        largura_plataforma_m=LARGURA_PLATAFORMA_M,
        talude_corte_h_v=TALUDE_CORTE_H_V,
        talude_aterro_h_v=TALUDE_ATERRO_H_V,
    ),
    janela_greide_m=JANELA_SUAVIZACAO_GREIDE_M,
    fator_conversao=FATOR_CONVERSAO_CORTE_ATERRO,
    passo_estacao_m=PASSO_ESTACA_M,
    resolucao_mde_m=RESOLUCAO_MDE_M,
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
    "Traçado existente": em_tracado(existente),
    "Alternativa por menor custo": em_tracado(
        [tuple(c) for c in alternativa["features"][0]["geometry"]["coordinates"]]
    ),
}

with ProvedorElevacaoRaster(MDE) as provedor:
    linhas = tuple(
        compor_linha(nome, extrair_perfil(tracado, provedor), PREMISSAS)
        for nome, tracado in tracados.items()
    )

relatorio = Relatorio(premissas=PREMISSAS, linhas=linhas)

print(
    f"Classe adotada: {CLASSE_ADOTADA.nome} "
    f"(rampa máxima {CLASSE_ADOTADA.rampa_maxima_pct:.1f}%)"
)
print(f"Janela do greide: {JANELA_SUAVIZACAO_GREIDE_M:.0f} m\n")

cabecalho = (
    f"{'Alternativa':<30}{'Ext (km)':>10}{'Relevo (m)':>12}{'Inadm (km)':>12}"
    f"{'Movim. (m3)':>14}{'m3/km':>10}{'Rampa greide':>14}"
)
print(cabecalho)
print("-" * len(cabecalho))
for linha in relatorio.linhas:
    print(
        f"{linha.resumo.nome:<30}{linha.resumo.extensao_km:>10.2f}"
        f"{linha.resumo.relevo_vencido_m:>12.0f}"
        f"{linha.resumo.extensao_inadmissivel_km:>12.2f}"
        f"{linha.volumes.movimentado_m3:>14,.0f}"
        f"{linha.volume_por_km:>10,.0f}"
        f"{linha.rampa_maxima_greide_pct:>13.2f}%"
    )

print("\nVariação em relação ao traçado existente:")
for indice in range(1, len(relatorio.linhas)):
    nome = relatorio.linhas[indice].resumo.nome
    print(f"  {nome}:")
    for rotulo, atributo in (
        ("extensão", "extensao_km"),
        ("relevo vencido", "relevo_vencido_m"),
        ("extensão inadmissível", "extensao_inadmissivel_km"),
        ("volume movimentado", "movimentado_m3"),
    ):
        variacao = relatorio.variacao_percentual(indice, atributo)
        print(f"    {rotulo}: {variacao:+.1f}%")

DESTINO.write_text(
    json.dumps(
        {
            "premissas": {
                "classe": CLASSE_ADOTADA.nome,
                "rampa_maxima_pct": CLASSE_ADOTADA.rampa_maxima_pct,
                "velocidade_diretriz_kmh": CLASSE_ADOTADA.velocidade_diretriz_kmh,
                "fonte_classe": CLASSE_ADOTADA.fonte,
                "largura_plataforma_m": LARGURA_PLATAFORMA_M,
                "talude_corte_h_v": TALUDE_CORTE_H_V,
                "talude_aterro_h_v": TALUDE_ATERRO_H_V,
                "janela_greide_m": JANELA_SUAVIZACAO_GREIDE_M,
                "fator_conversao": FATOR_CONVERSAO_CORTE_ATERRO,
                "passo_estacao_m": PASSO_ESTACA_M,
                "resolucao_mde_m": RESOLUCAO_MDE_M,
            },
            "alternativas": [
                {
                    "nome": linha.resumo.nome,
                    "extensao_km": linha.resumo.extensao_km,
                    "subida_acumulada_m": linha.resumo.subida_acumulada_m,
                    "descida_acumulada_m": linha.resumo.descida_acumulada_m,
                    "relevo_vencido_m": linha.resumo.relevo_vencido_m,
                    "desnivel_liquido_m": linha.resumo.desnivel_liquido_m,
                    "rampa_maxima_terreno_pct": linha.resumo.rampa_maxima_pct,
                    "extensao_inadmissivel_km": linha.resumo.extensao_inadmissivel_km,
                    "rampa_maxima_greide_pct": linha.rampa_maxima_greide_pct,
                    "segmentos_greide_inadmissiveis": (
                        linha.segmentos_greide_inadmissiveis
                    ),
                    "corte_m3": linha.volumes.corte_m3,
                    "aterro_m3": linha.volumes.aterro_m3,
                    "movimentado_m3": linha.volumes.movimentado_m3,
                    "saldo_m3": linha.volumes.saldo_m3,
                    "compensado": linha.volumes.compensado,
                    "volume_por_km": linha.volume_por_km,
                    "maior_aterro_m": linha.maior_aterro_m,
                    "maior_corte_m": linha.maior_corte_m,
                }
                for linha in relatorio.linhas
            ],
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(f"\nGravado: {DESTINO}")
