"""Representação gráfica do perfil longitudinal.

Não realiza cálculo de engenharia: recebe um perfil pronto e o desenha.
O exagero vertical é convenção de projeto rodoviário, necessário para
tornar o relevo legível, e por isso é sempre declarado na figura.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bambui_luz.domain.perfil import PerfilLongitudinal

EXAGERO_VERTICAL_PADRAO = 10.0
"""Razão entre as escalas vertical e horizontal na figura."""


def desenhar_perfil(
    perfil: PerfilLongitudinal,
    destino: Path,
    titulo: str,
    rampa_limite_pct: float | None = None,
    exagero_vertical: float = EXAGERO_VERTICAL_PADRAO,
) -> Path:
    """Desenha o perfil longitudinal e o diagrama de rampas.

    Args:
        perfil: Perfil a representar.
        destino: Caminho do arquivo de imagem a gravar.
        titulo: Título da figura.
        rampa_limite_pct: Limite de rampa a destacar no diagrama inferior.
            Quando None, nenhuma referência é traçada.
        exagero_vertical: Razão entre escalas vertical e horizontal.

    Returns:
        Caminho da figura gravada.
    """
    distancias_km = [e.distancia_m / 1000 for e in perfil.estacoes]
    cotas = [e.cota_m for e in perfil.estacoes]
    rampas = perfil.rampas()
    meios_km = [
        (perfil.estacoes[i].distancia_m + perfil.estacoes[i + 1].distancia_m) / 2000
        for i in range(len(rampas))
    ]

    figura, (eixo_perfil, eixo_rampa) = plt.subplots(
        2, 1, figsize=(14, 8), height_ratios=[3, 1], sharex=True
    )

    eixo_perfil.plot(distancias_km, cotas, linewidth=1.2, color="#8B4513")
    eixo_perfil.fill_between(distancias_km, min(cotas) - 5, cotas, color="#D2B48C")
    eixo_perfil.set_ylabel("Cota (m)")
    eixo_perfil.set_title(titulo)
    eixo_perfil.grid(visible=True, linewidth=0.3, alpha=0.5)
    eixo_perfil.set_ylim(min(cotas) - 5, max(cotas) + 5)

    eixo_rampa.bar(meios_km, rampas, width=0.08, color="#4682B4")
    eixo_rampa.axhline(0, linewidth=0.8, color="black")
    if rampa_limite_pct is not None:
        for sinal in (1, -1):
            eixo_rampa.axhline(
                sinal * rampa_limite_pct,
                linewidth=0.8,
                color="#B22222",
                linestyle="--",
            )
    eixo_rampa.set_ylabel("Rampa (%)")
    eixo_rampa.set_xlabel("Distância (km)")
    eixo_rampa.grid(visible=True, linewidth=0.3, alpha=0.5)

    extensao_km = perfil.extensao / 1000
    amplitude_m = max(cotas) - min(cotas)
    figura.text(
        0.01,
        0.01,
        f"Exagero vertical aproximado: {exagero_vertical:.0f}x  |  "
        f"Extensão: {extensao_km:.2f} km  |  Amplitude: {amplitude_m:.1f} m",
        fontsize=8,
        color="#555555",
    )

    destino.parent.mkdir(parents=True, exist_ok=True)
    figura.tight_layout()
    figura.savefig(destino, dpi=150)
    plt.close(figura)
    return destino
