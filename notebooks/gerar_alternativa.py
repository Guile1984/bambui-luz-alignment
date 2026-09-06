"""Geração da alternativa de traçado por menor custo.

A superfície de custo combina declividade e posição topográfica. A
penalidade de talvegue corrige um defeito identificado na versão anterior:
com custo baseado apenas em declividade, o caminho ótimo descia ao fundo
de vale, onde o terreno é plano, ignorando os custos de drenagem,
travessia e restrição ambiental que a declividade não representa.

O resultado é um corredor de estudo, não um eixo geométrico: o caminho
avança por células de 30 m em oito direções possíveis.

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
DESTINO = Path("data/processed/alternativa_menor_custo.geojson")

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
print(f"Célula: {largura_m:.1f} m (leste-oeste) x {altura_m:.1f} m (norte-sul)")

declividade = calcular_declividade(cotas, largura_m, altura_m)
posicao = calcular_posicao_topografica(cotas, RAIO_POSICAO_TOPOGRAFICA_CELULAS)

validas = declividade[~np.isnan(declividade)]
print("\nDeclividade do corredor:")
print(f"  mediana: {np.median(validas):.1f}%")
print(
    f"  acima de {DECLIVIDADE_BARREIRA_PCT:.0f}%: "
    f"{100 * (validas > DECLIVIDADE_BARREIRA_PCT).mean():.1f}% das células"
)

posicoes_validas = posicao[~np.isnan(posicao)]
print(
    "\nPosição topográfica do corredor "
    f"(raio {RAIO_POSICAO_TOPOGRAFICA_CELULAS * 30} m):"
)
print(f"  mediana: {np.median(posicoes_validas):+.1f} m")
print(f"  faixa: {posicoes_validas.min():+.1f} a {posicoes_validas.max():+.1f} m")
print(
    f"  células rebaixadas mais de {POSICAO_REFERENCIA_M:.0f} m: "
    f"{100 * (posicoes_validas < -POSICAO_REFERENCIA_M).mean():.1f}%"
)

custo = compor_custo(
    declividade,
    DECLIVIDADE_REFERENCIA_PCT,
    PESO_DECLIVIDADE,
    DECLIVIDADE_BARREIRA_PCT,
    CUSTO_BARREIRA,
    posicao_topografica_m=posicao,
    posicao_referencia_m=POSICAO_REFERENCIA_M,
    peso_talvegue=PESO_TALVEGUE,
)

print(f"\nOrigem (Bambuí): célula {origem_celula}")
print(f"Destino (Esteios): célula {destino_celula}")

caminho, custo_total = caminho_de_menor_custo(custo, origem_celula, destino_celula)
print(f"\nCélulas no caminho: {len(caminho):,}")
print(f"Custo acumulado: {custo_total:,.0f}")
print(f"Custo médio por célula: {custo_total / len(caminho):.2f}")

cotas_caminho = [float(cotas[linha, coluna]) for linha, coluna in caminho]
posicoes_caminho = [
    float(posicao[linha, coluna])
    for linha, coluna in caminho
    if not np.isnan(posicao[linha, coluna])
]
print(f"\nCota mediana do caminho: {np.median(cotas_caminho):.1f} m")
print(f"Posição topográfica mediana: {np.median(posicoes_caminho):+.1f} m")
print(
    f"Pontos abaixo da vizinhança: {100 * (np.array(posicoes_caminho) < 0).mean():.1f}%"
)

coordenadas = [
    list(rasterio.transform.xy(transformacao, linha, coluna))
    for linha, coluna in caminho
]

DESTINO.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "nome": "alternativa por menor custo",
                        "peso_declividade": PESO_DECLIVIDADE,
                        "declividade_referencia_pct": DECLIVIDADE_REFERENCIA_PCT,
                        "declividade_barreira_pct": DECLIVIDADE_BARREIRA_PCT,
                        "peso_talvegue": PESO_TALVEGUE,
                        "posicao_referencia_m": POSICAO_REFERENCIA_M,
                        "raio_posicao_celulas": RAIO_POSICAO_TOPOGRAFICA_CELULAS,
                    },
                    "geometry": {"type": "LineString", "coordinates": coordenadas},
                }
            ],
        }
    ),
    encoding="utf-8",
)
print(f"\nGravado: {DESTINO}")
