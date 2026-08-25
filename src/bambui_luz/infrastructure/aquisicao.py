"""Aquisição de tiles do modelo digital de elevação Copernicus GLO-30.

Os dados são obtidos do repositório público em nuvem, sem necessidade de
credencial. O download é idempotente: tiles já presentes em disco não são
baixados novamente.

Os dados Copernicus DEM são disponibilizados sob licença gratuita que exige
declaração de fonte. O aviso de atribuição exigido deve constar do README.
"""

import math
import urllib.request
from collections.abc import Iterable
from pathlib import Path

BASE_GLO30 = "https://copernicus-dem-30m.s3.amazonaws.com"
"""Repositório público dos tiles GLO-30, formato COG."""


def nome_tile(latitude_graus: float, longitude_graus: float) -> str:
    """Determina o tile GLO-30 que contém o ponrto informado.

    Os tiles cobrem 1 grau em cada direção e são identificados pelo canto
    sudoeste em graus inteiros, o que exige piso e não arredondamento.

    Args:
        latitude_graus: Latitude em graus decimais, negativa ao sul.
        longitude_graus: Longitude em graus decimais, negativa a oeste.

    Returns:
        Identificador do tile, como "Copernicus_DSM_COG_10_S21_00_W046_00_DEM"
    """
    lat_piso = math.floor(latitude_graus)
    lon_piso = math.floor(longitude_graus)
    hemisferio_ns = "N" if lat_piso >= 0 else "S"
    hemisferio_ew = "E" if lon_piso >= 0 else "W"
    return (
        f"Copernicus_DSM_COG_10_"
        f"{hemisferio_ns}{abs(lat_piso):02d}_00_"
        f"{hemisferio_ew}{abs(lon_piso):03d}_00_DEM"
    )


def tiles_necessarios(coordenadas: Iterable[tuple[float, float]]) -> tuple[str, ...]:
    """Reúne os tiles distintos necessários para cobrir as coordenadas.

    Args:
        coordenadas: Pares de latitude e longitude em graus decimais.

    Returns:
        Identificadores de tile, sem repetição e em ordem alfabética.
    """
    return tuple(sorted({nome_tile(lat, lon) for lat, lon in coordenadas}))


def url_tile(nome: str) -> str:
    """Monta a URL pública de um tile.

    Args:
        nome: Identificador do tile.

    Returns:
        URL completa do arquivo GeoTIFF.
    """
    return f"{BASE_GLO30}/{nome}/{nome}.tif"


def baixar_tile(nome: str, destino: Path) -> Path:
    """Baixar um tile, caso ainda não esteja presente em disco.

    A operação é idempotente: se o arquivo já existir, nada é feito.

    Args:
        nome: Identificador do tile.
        destino: Diretório onde o arquivo será gravado.

    Returns:
        Caminho do arquivo em disco.
    """
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / f"{nome}.tif"
    if caminho.exists():
        return caminho
    urllib.request.urlretrieve(url_tile(nome), caminho)
    return caminho
