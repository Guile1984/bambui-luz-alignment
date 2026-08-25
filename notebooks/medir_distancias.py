"""Medição das distâncias entre as localidades de referência.

Script exploratório. Substitui estimativas manuais por valores calculados,
que serão transcritos para a seção de revisões de premissa do README.
"""

from itertools import combinations

from pyproj import Geod

from bambui_luz.config.estudo import BAMBUI, ESTEIOS, LUZ
from bambui_luz.infrastructure.coordenadas import local_para_ponto

LOCAIS = [BAMBUI, ESTEIOS, LUZ]
geodesico = Geod(ellps="GRS80")

print("Distâncias em linha reta entre as localidades de referência\n")
print(f"{'Trecho':<22}{'Geodésica (km)':>16}{'Projetada (km)':>16}{'Δ (m)':>10}")

for origem, destino in combinations(LOCAIS, 2):
    _, _, geo_m = geodesico.inv(
        origem.longitude_graus,
        origem.latitude_graus,
        destino.longitude_graus,
        destino.latitude_graus,
    )
    proj_m = local_para_ponto(origem).distancia_ate(local_para_ponto(destino))
    trecho = f"{origem.nome} - {destino.nome}"
    print(
        f"{trecho:<22}{geo_m / 1000:>16.3f}"
        f"{proj_m / 1000:>16.3f}{proj_m - geo_m:>10.1f}"
    )

soma_km = 0.0
for origem, destino in [(BAMBUI, ESTEIOS), (ESTEIOS, LUZ)]:
    _, _, geo_m = geodesico.inv(
        origem.longitude_graus,
        origem.latitude_graus,
        destino.longitude_graus,
        destino.latitude_graus,
    )
    soma_km += geo_m / 1000

print(f"\nBambuí - Esteios - Luz (soma dos trechos): {soma_km:.3f} km")

print("\nDesníveis segundo as altitudes do IBGE:")
for origem, destino in combinations(LOCAIS, 2):
    if origem.altitude_ibge_m is not None and destino.altitude_ibge_m is not None:
        desnivel = destino.altitude_ibge_m - origem.altitude_ibge_m
        print(f"  {origem.nome} → {destino.nome}: {desnivel:+.1f} m")
