"""Análise de sensibilidade do traçado aos dois pesos da superfície de custo.

A penalidade de talvegue foi introduzida para corrigir um defeito de
modelo: com custo baseado apenas em declividade, o caminho ótimo descia ao
fundo de vale. Seu peso foi arbitrado, e esta varredura verifica se a
correção é robusta ou se depende do valor escolhido.

O peso de talvegue igual a zero reproduz o modelo anterior e serve de
controle da varredura.

Dados de elevação Copernicus DEM.
"""

import json
from pathlib import Path

import numpy as np
import rasterio

from bambui_luz.config.estudo import (
    BAMBUI,
    CUSTO_BARREIRA,
    DECLIVIDADE_BARREIRA_PCT,
    DECLIVIDADE_REFERENCIA_PCT,
    ESTEIOS,
    PESO_DECLIVIDADE,
    PESO_TALVEGUE,
    POSICAO_REFERENCIA_M,
    RAIO_POSICAO_TOPOGRAFICA_CELULAS,
)
from bambui_luz.infrastructure.superficie import (
    calcular_declividade,
    calcular_posicao_topografica,
    compor_custo,
    dimensoes_celula_m,
)
from bambui_luz.infrastructure.tracado_otimo import caminho_de_menor_custo

MDE = Path("data/processed/mde_corredor.tif")
DESTINO = Path("data/processed/sensibilidade.json")

PESOS_DECLIVIDADE = [2.0, 4.0, 8.0]
PESOS_TALVEGUE = [0.0, 1.0, 3.0, 6.0, 12.0]

with rasterio.open(MDE) as raster:
    cotas = raster.read(1)
    transformacao = raster.transform
    limites = raster.bounds
    origem = raster.index(BAMBUI.longitude_graus, BAMBUI.latitude_graus)
    destino = raster.index(ESTEIOS.longitude_graus, ESTEIOS.latitude_graus)

latitude_media = (limites.bottom + limites.top) / 2
largura_m, altura_m = dimensoes_celula_m(
    abs(transformacao.a), abs(transformacao.e), latitude_media
)
declividade = calcular_declividade(cotas, largura_m, altura_m)
posicao = calcular_posicao_topografica(cotas, RAIO_POSICAO_TOPOGRAFICA_CELULAS)

print(
    f"Varredura: {len(PESOS_DECLIVIDADE)} x {len(PESOS_TALVEGUE)} = "
    f"{len(PESOS_DECLIVIDADE) * len(PESOS_TALVEGUE)} combinações\n"
)

resultados = []
caminhos = {}
for peso_decl in PESOS_DECLIVIDADE:
    for peso_talv in PESOS_TALVEGUE:
        custo = compor_custo(
            declividade,
            DECLIVIDADE_REFERENCIA_PCT,
            peso_decl,
            DECLIVIDADE_BARREIRA_PCT,
            CUSTO_BARREIRA,
            posicao_topografica_m=posicao,
            posicao_referencia_m=POSICAO_REFERENCIA_M,
            peso_talvegue=peso_talv,
        )
        caminho, _ = caminho_de_menor_custo(custo, origem, destino)
        caminhos[(peso_decl, peso_talv)] = set(caminho)

        posicoes = [
            float(posicao[linha, coluna])
            for linha, coluna in caminho
            if not np.isnan(posicao[linha, coluna])
        ]
        cotas_caminho = [float(cotas[linha, coluna]) for linha, coluna in caminho]
        resultados.append(
            {
                "peso_declividade": peso_decl,
                "peso_talvegue": peso_talv,
                "celulas": len(caminho),
                "cota_mediana_m": float(np.median(cotas_caminho)),
                "posicao_mediana_m": float(np.median(posicoes)),
                "fracao_rebaixada": float((np.array(posicoes) < 0).mean()),
            }
        )

cabecalho = (
    f"{'P.decl':>8}{'P.talv':>8}{'Células':>9}{'Cota (m)':>10}"
    f"{'Posição (m)':>13}{'Rebaixado':>11}{'Situação':>14}"
)
print(cabecalho)
print("-" * len(cabecalho))
for r in resultados:
    situacao = "vale" if r["posicao_mediana_m"] < 0 else "divisor"
    print(
        f"{r['peso_declividade']:>8.0f}{r['peso_talvegue']:>8.0f}"
        f"{r['celulas']:>9,}{r['cota_mediana_m']:>10.1f}"
        f"{r['posicao_mediana_m']:>+13.1f}"
        f"{100 * r['fracao_rebaixada']:>10.1f}%{situacao:>14}"
    )

adotado = caminhos[(PESO_DECLIVIDADE, PESO_TALVEGUE)]
print(
    f"\nSobreposição com o traçado adotado "
    f"(declividade {PESO_DECLIVIDADE:g}, talvegue {PESO_TALVEGUE:g}):\n"
)
print(f"{'P.decl':>8}{'P.talv':>8}{'Comum':>9}")
print("-" * 25)
for (peso_decl, peso_talv), celulas in caminhos.items():
    comuns = len(celulas & adotado)
    menor = min(len(celulas), len(adotado))
    print(f"{peso_decl:>8.0f}{peso_talv:>8.0f}{100 * comuns / menor:>8.0f}%")

DESTINO.write_text(
    json.dumps(
        {
            "raio_posicao_celulas": RAIO_POSICAO_TOPOGRAFICA_CELULAS,
            "posicao_referencia_m": POSICAO_REFERENCIA_M,
            "declividade_referencia_pct": DECLIVIDADE_REFERENCIA_PCT,
            "declividade_barreira_pct": DECLIVIDADE_BARREIRA_PCT,
            "adotado": {
                "peso_declividade": PESO_DECLIVIDADE,
                "peso_talvegue": PESO_TALVEGUE,
            },
            "resultados": resultados,
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(f"\nGravado: {DESTINO}")
