"""Representação gráfica do diagrama de massa.

Não realiza cálculo: recebe perfil, greide e curva prontos e os desenha.
"""

from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bambui_luz.domain.greide import Greide
from bambui_luz.domain.perfil import PerfilLongitudinal

COR_CORTE = "#A0522D"
"""Cor das áreas de corte."""

COR_ATERRO = "#4682B4"
"""Cor das áreas de aterro"""


def desenhar_massa(
    perfil: PerfilLongitudinal,
    greide: Greide,
    alturas_m: Sequence[float],
    ordenadas_m3: Sequence[float],
    destino: Path,
    titulo: str,
) -> Path:
    """Desenhar perfil, greide, alturas de trabalho e curva de massa.

    Args:
        perfil: Perfil do terreno natural.
        greide: Greide de projeto.
        alturas_m: Alturas de trabalho por estação, positivas em aterro.
        ordenadas_m3: Ordenadas da curva de uma massa, uma por estação.
        destino: Caminho do arquivo de imagem a gravar.
        titulo: Título da figura.

    Returns:
        Caminho da figura gravada.
    """
    distancias_km = [e.distancia_m / 1000 for e in perfil.estacoes]
    cotas_terreno = [e.cota_m for e in perfil.estacoes]
    cotas_greide = [e.cota_m for e in greide.estacoes]

    figura, (eixo_perfil, eixo_altura, eixo_massa) = plt.subplots(
        3, 1, figsize=(15, 11), height_ratios=[3, 1, 2], sharex=True
    )
    eixo_perfil.plot(
        distancias_km,
        cotas_terreno,
        linewidth=1.0,
        color="#555555",
        label="Terrno natural",
    )
    eixo_perfil.plot(
        distancias_km,
        cotas_greide,
        linewidth=1.6,
        color="#B22222",
        label="Greide de projeto",
    )
    eixo_perfil.fill_between(
        distancias_km,
        cotas_terreno,
        cotas_greide,
        where=[g < t for g, t in zip(cotas_greide, cotas_terreno, strict=True)],
        color=COR_CORTE,
        alpha=0.5,
        label="Corte",
    )
    eixo_perfil.fill_between(
        distancias_km,
        cotas_terreno,
        cotas_greide,
        where=[g >= t for g, t in zip(cotas_greide, cotas_terreno, strict=True)],
        color=COR_ATERRO,
        alpha=0.5,
        label="Aterro",
    )
    eixo_perfil.set_ylabel("Cota (m)")
    eixo_perfil.set_title(titulo)
    eixo_perfil.legend(loc="upper right", fontsize=8)
    eixo_perfil.grid(visible=True, linewidth=0.3, alpha=0.5)

    cores = [COR_ATERRO if altura > 0 else COR_CORTE for altura in alturas_m]
    eixo_altura.bar(distancias_km, alturas_m, width=0.09, color=cores)
    eixo_altura.axhline(0, linewidth=0.8, color="black")
    eixo_altura.set_ylabel("Altura (m)")
    eixo_altura.grid(visible=True, linewidth=0.3, alpha=0.5)

    ordenadas_mil = [ordenada / 1000 for ordenada in ordenadas_m3]
    eixo_massa.plot(distancias_km, ordenadas_mil, linewidth=1.4, color="#2D6A4F")
    eixo_massa.fill_between(distancias_km, 0, ordenadas_mil, color="#2D6A4F", alpha=0.2)
    eixo_massa.axhline(0, linewidth=0.8, color="black")
    eixo_massa.set_ylabel("Curva de massa (mil m³)")
    eixo_massa.set_xlabel("Distância (km)")
    eixo_massa.grid(visible=True, linewidth=0.3, alpha=0.5)

    figura.text(
        0.01,
        0.005,
        "Volumes obtidos de greide simplificado sobre modelo de elevação de "
        "30 m. Prestam-se à comparação relativa entre alternativas.",
        fontsize=8,
        color="#555555",
    )

    destino.parent.mkdir(parents=True, exist_ok=True)
    figura.tight_layout()
    figura.savefig(destino, dpi=150)
    plt.close(figura)
    return destino
