"""Composição e recorte do modelo digital de elevação.

Os tiles são unidos e recortados à extensão do corredor de estudo,
permanecendo no sistema de referência geográfico da fonte. A reprojeção
não é aplicada ao raster: reamostrar todos os pixels acrescentaria uma
interpolação entre a fonte e o resultado, impossível de separar depois.
"""

from collections.abc import Sequence
from pathlib import Path

import rasterio
from rasterio.merge import merge

from bambui_luz.config.estudo import LocalNotavel

METROS_POR_GRAU_LATITUDE = 111_320.0
"""Comprimento aproximado de um grau de latitude, em metros."""


def extensao_com_margem(
    locais: Sequence[LocalNotavel], margem_m: float
) -> tuple[float, float, float, float]:
    """Calcula a extensão geográfica que contém os locais, com folga.

    A conversão de metros para graus é aproximada e deliberadamente
    conservadora: para a longitude, adota-se o mesmo fator da latitude,
    o que superestima a margem em qualquer latitude fora do equador.
    Uma margem maior que a pedida é inofensiva; menor não seria.

    Args:
        locais: Localidades que devem estar contidas na extensão.
        margem_m: Folga a acrescentar em cada direção, em metros.

    Returns:
        Extensão como (oeste, sul, leste, norte), em graus decimais.

    Raises:
        ValueError: Se nenhum local for informado.
    """
    if not locais:
        raise ValueError("é necessário ao menos um local para definir a extensão")
    margem_graus = margem_m / METROS_POR_GRAU_LATITUDE
    latitudes = [local.latitude_graus for local in locais]
    longitudes = [local.longitude_graus for local in locais]
    return (
        min(longitudes) - margem_graus,
        min(latitudes) - margem_graus,
        max(longitudes) + margem_graus,
        max(latitudes) + margem_graus,
    )


def compor_recorte(
    tiles: Sequence[Path],
    extensao: tuple[float, float, float, float],
    destino: Path,
) -> Path:
    """Une os tiles e grava o recorte da extensão informada.

    Args:
        tiles: Caminhos dos arquivos a unir.
        extensao: Limites como (oeste, sul, leste, norte) em graus.
        destino: Caminho do arquivo a gravar.

    Returns:
        Caminho do recorte gravado.

    Raises:
        ValueError: Se nenhume tile for informado.
    """
    if not tiles:
        raise ValueError("é necessário ao menos um tile para compor o recorte")
    fontes = [rasterio.open(caminho) for caminho in tiles]
    try:
        matriz, transformacao = merge(fontes, bounds=extensao)
        perfil = fontes[0].profile.copy()
    finally:
        for fonte in fontes:
            fonte.close()

    perfil.update(
        height=matriz.shape[1],
        width=matriz.shape[2],
        transform=transformacao,
        compress="deflate",
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(destino, "w", **perfil) as saida:
        saida.write(matriz)
    return destino
