"""Representação cartográfica de traçados sobre superfície de fundo.

Não realiza cálculo: recebe superfície e geometrias prontas e as desenha.
O fundo de declividade permite avaliar visualmente se um traçado evita as
encostas, o que é diagnóstico da composição da superfície de custo.
"""

from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CORES = ["#00A0A0", "#1E6091", "#2D6A4F", "#7B2CBF"]
"""Cores dos traçados, na ordem em que forem informados."""


def desenhar_mapa(
    fundo: np.ndarray,
    extensao: tuple[float, float, float, float],
    tracados: dict[str, Sequence[tuple[float, float]]],
    pontos: dict[str, tuple[float, float]],
    destino: Path,
    titulo: str,
    rotulo_fundo: str = "Declividade (%)",
    limite_fundo: float = 30.0,
) -> Path:
    """Desenha traçados e pontos notáveis sobre uma superfície de fundo.

    Args:
        fundo: Grade a representar como imagem de fundo.
        extensao: Limites geográficos como (oeste, leste, sul, norte).
        tracados: Nome de cada traçado e sua sequência de coordenadas
            (longitude, latitude).
        pontos: Nome e coordenadas (longitude, latitude) de cada ponto
            notável a marcar.
        titulo: Título da figura.
        destino: Local onde será salvo a figura
        rotulo_fundo: Legenda da barra de cores.
        limite_fundo: Valor máximo da escala de cores do fundo.

    Returns:
        Caminho da figura gravada.
    """
    figura, eixo = plt.subplots(figsize=(14, 9))

    imagem = eixo.imshow(
        fundo,
        extent=extensao,
        cmap="YlOrRd",
        vmin=0,
        vmax=limite_fundo,
        origin="upper",
        aspect="auto",
    )
    figura.colorbar(imagem, ax=eixo, label=rotulo_fundo, shrink=0.7)

    for indice, (nome, coordenadas) in enumerate(tracados.items()):
        longitudes = [c[0] for c in coordenadas]
        latitudes = [c[1] for c in coordenadas]
        eixo.plot(
            longitudes,
            latitudes,
            linewidth=1.8,
            color=CORES[indice % len(CORES)],
            label=nome,
        )

    for nome, (longitude, latitude) in pontos.items():
        eixo.plot(longitude, latitude, "o", color="black", markersize=7)
        eixo.annotate(
            nome,
            (longitude, latitude),
            textcoords="offset points",
            xytext=(8, 6),
            fontsize=10,
            fontweight="bold",
        )

    eixo.set_title(titulo)
    eixo.set_xlabel("Longitude")
    eixo.set_ylabel("Latitude")
    eixo.legend(loc="best")
    eixo.grid(visible=True, linewidth=0.3, alpha=0.4)

    destino.parent.mkdir(parents=True, exist_ok=True)
    figura.tight_layout()
    figura.savefig(destino, dpi=150)
    plt.close(figura)
    return destino
