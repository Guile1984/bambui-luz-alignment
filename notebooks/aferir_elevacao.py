"""Aferição do modelo de elevação contra altitudes oficiais do IBGE.

Compara a cota lida do raster nas três localidades de referência com a
altitude publicada no Cadastro de Localidades Selecionadas. Verificação
independente da cadeia coordenadas, projeção e leitura.
"""

from pathlib import Path

from bambui_luz.config.estudo import BAMBUI, ESTEIOS, LUZ
from bambui_luz.infrastructure.coordenadas import local_para_ponto
from bambui_luz.infrastructure.mde import ProvedorElevacaoRaster

CAMINHO = Path("data/processed/mde_corredor.tif")
LOCAIS = [BAMBUI, ESTEIOS, LUZ]

pontos = [local_para_ponto(local) for local in LOCAIS]

with ProvedorElevacaoRaster(CAMINHO) as provedor:
    cotas = provedor.cotas_em(pontos)

print(f"{'Local':<12}{'IBGE (m)':>12}{'MDE (m)':>12}{'Diferença':>12}")
for local, cota in zip(LOCAIS, cotas, strict=True):
    diferenca = cota - local.altitude_ibge_m
    print(
        f"{local.nome:<12}{local.altitude_ibge_m:>12.1f}"
        f"{cota:>12.1f}{diferenca:>+12.1f}"
    )

diferencas = [
    cota - local.altitude_ibge_m for local, cota in zip(LOCAIS, cotas, strict=True)
]
maior = max(abs(d) for d in diferencas)
media = sum(diferencas) / len(diferencas)

print(f"\nMaior diferença absoluta: {maior:.1f} m")
print(f"Diferença média (viés): {media:+.1f} m")

if maior > 50:
    print("\nATENÇÃO: diferença acima do esperado. Investigar antes de prosseguir.")
elif maior > 15:
    print("\nDiferença acima do típico, porem plausível. Registrar no NOTES.md.")
else:
    print("\nDiferenças dentro do esperado para MDE de 30 m.")
