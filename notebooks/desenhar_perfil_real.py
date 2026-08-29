"""Gera a figura do perfil longitudinal do traçado real Bambuí-Esteios."""

import json
from pathlib import Path

from bambui_luz.domain.perfil import PerfilLongitudinal, PontoPerfil
from bambui_luz.presentation.grafico_perfil import desenhar_perfil

ORIGEM = Path("data/processed/perfil_bambui_esteios.json")
DESTINO = Path("data/processed/perfil_bambui_esteios.png")

dados = json.loads(ORIGEM.read_text(encoding="utf-8"))
perfil = PerfilLongitudinal(
    estacoes=tuple(
        PontoPerfil(distancia_m=d["distancia_m"], cota_m=d["cota_m"]) for d in dados
    )
)

caminho = desenhar_perfil(
    perfil,
    DESTINO,
    titulo="Perfil Longitudinal do terreno - Bambuí a Esteios (traçado existente)",
    rampa_limite_pct=5.0,
)
print(f"Figura gravada: {caminho}")
