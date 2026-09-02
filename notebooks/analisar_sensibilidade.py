"""Análise de sensibilidade do traçado gerado aos pesos de custo.

Os pesos da superfície de custo são valores arbitrados. Esta análise
verifica se as decisões de traçado decorrem do terreno ou dos parâmetros
escolhidos: traçados semelhantes sob pesos distintos indicam corredor
robusto; traçados divergentes indicam que o resultado é artefato dos
parâmetros.

Dados de elevação Copernicus DEM.
"""

import json
from pathlib import Path

import rasterio

from bambui_luz.config.estudo import (
    BAMBUI,
    CLASSE_ADOTADA,
    CRS_GEOGRAFICO,
    CRS_TRABALHO,
    CUSTO_BARREIRA,
    DECLIVIDADE_BARREIRA_PCT,
    DECLIVIDADE_REFERENCIA_PCT,
    ESTEIOS,
)
from bambui_luz.domain.geometria import Ponto, Tracado
from bambui_luz.infrastructure.coordenadas import criar_transformador
from bambui_luz.infrastructure.mde import ProvedorElevacaoRaster
from bambui_luz.infrastructure.superficie import (
    calcular_declividade,
    compor_custo,
    dimensoes_celula_m,
)
from bambui_luz.infrastructure.tracado_otimo import caminho_de_menor_custo
from bambui_luz.services.comparar_alternativas import resumir
from bambui_luz.services.extrair_perfil import extrair_perfil

MDE = Path("data/processed/mde_corredor.tif")
DESTINO = Path("data/processed/sensibilidade.json")
PESOS = [0.0, 1.0, 2.0, 4.0, 8.0, 16.0]


with rasterio.open(MDE) as raster:
    cotas = raster.read(1)
    transformacao = raster.transform
    limites = raster.bounds
    origem_celula = raster.index(BAMBUI.longitude_graus, BAMBUI.latitude_graus)
    destino_celula = raster.index(ESTEIOS.longitude_graus, ESTEIOS.latitude_graus)

latitude_media = (limites.bottom + limites.top) / 2
largura_m, altura_m = dimensoes_celula_m(
    abs(transformacao.a), abs(transformacao.e), latitude_media
)
declividade = calcular_declividade(cotas, largura_m, altura_m)
para_metros = criar_transformador(CRS_GEOGRAFICO, CRS_TRABALHO)

resultados = []
caminhos = {}

with ProvedorElevacaoRaster(MDE) as provedor:
    for peso in PESOS:
        custo = compor_custo(
            declividade,
            DECLIVIDADE_REFERENCIA_PCT,
            peso,
            DECLIVIDADE_BARREIRA_PCT,
            CUSTO_BARREIRA,
        )
        caminho, _ = caminho_de_menor_custo(custo, origem_celula, destino_celula)
        caminhos[peso] = set(caminho)

        pontos = []
        for linha, coluna in caminho:
            longitude, latitude = rasterio.transform.xy(transformacao, linha, coluna)
            x, y = para_metros.transform(longitude, latitude)
            pontos.append(Ponto(x=x, y=y))

        perfil = extrair_perfil(Tracado(pontos=tuple(pontos)), provedor)
        resumo = resumir(f"peso {peso:g}", perfil, CLASSE_ADOTADA)
        resultados.append((peso, resumo, len(caminho)))

cabecalho = (
    f"{'Peso':>6}{'Células':>9}{'Ext (km)':>10}{'Relevo (m)':>12}"
    f"{'Rampa máx':>11}{'Inadm (km)':>12}"
)
print(cabecalho)
print("-" * len(cabecalho))
for peso, r, celulas in resultados:
    print(
        f"{peso:>6.0f}{celulas:>9,}{r.extensao_km:>10.2f}"
        f"{r.relevo_vencido_m:>12.0f}{r.rampa_maxima_pct:>10.2f}%"
        f"{r.extensao_inadmissivel_km:>12.2f}"
    )

print("\nFração de células compartilhadas entre pares de traçados:")
print(f"{'':>8}" + "".join(f"{p:>8.0f}" for p in PESOS))
for peso_a in PESOS:
    linha = f"{peso_a:>8.0f}"
    for pesos_b in PESOS:
        comuns = len(caminhos[peso_a]) & len(caminhos[pesos_b])
        menor = min(len(caminhos[peso_a]), len(caminhos[pesos_b]))
        linha += f"{100 * comuns / menor:>7.0f}%"
    print(linha)

DESTINO.write_text(
    json.dumps(
        {
            "declividade_referencia_pct": DECLIVIDADE_REFERENCIA_PCT,
            "declividade_barreira_pct": DECLIVIDADE_BARREIRA_PCT,
            "resultados": [
                {
                    "peso_declividade": peso,
                    "celulas": celulas,
                    "extensao_km": r.extensao_km,
                    "relevo_vencido_m": r.relevo_vencido_m,
                    "rampa_maxima_pct": r.rampa_maxima_pct,
                    "extensao_inadmissivel_km": r.extensao_inadmissivel_km,
                }
                for peso, r, celulas in resultados
            ],
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(f"\nGravado: {DESTINO}")
