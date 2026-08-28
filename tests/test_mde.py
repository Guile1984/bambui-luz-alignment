"""Testes da leitura de elevação a partir de raster."""

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from bambui_luz.config.estudo import BAMBUI
from bambui_luz.domain.geometria import Ponto
from bambui_luz.infrastructure.coordenadas import local_para_ponto
from bambui_luz.infrastructure.mde import ProvedorElevacaoRaster
from bambui_luz.ports.elevacao import ElevacaoIndisponivelError, ProvedorElevacao

LADO_CELULA_GRAUS = 0.001
ORIGEM_LON = -46.05
ORIGEM_LAT = -19.95


@pytest.fixture
def raster_sintetico(tmp_path: Path) -> Path:
    """Cria um raster 100x100 cobrindo a região de Bambuí.

    A cota cresce 1 m por coluna a partir de 600 m, e a célula (0, 0)
    recebe zero para exercitar a detecção de dado ausente.
    """
    cotas = np.zeros((100, 100), dtype="float32")
    for coluna in range(100):
        cotas[:, coluna] = 600.0 + coluna
    cotas[0, 0] = 0.0

    caminho = tmp_path / "sintetico.tif"
    with rasterio.open(
        caminho,
        "w",
        driver="GTiff",
        height=100,
        width=100,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(
            ORIGEM_LON, ORIGEM_LAT, LADO_CELULA_GRAUS, LADO_CELULA_GRAUS
        ),
    ) as saida:
        saida.write(cotas, 1)
    return caminho


def test_provedor_raster_satisfaz_o_contrato(raster_sintetico):
    with ProvedorElevacaoRaster(raster_sintetico) as provedor:
        assert isinstance(provedor, ProvedorElevacao)


def test_le_cota_de_ponto_coberto(raster_sintetico):
    ponto = local_para_ponto(BAMBUI)
    with ProvedorElevacaoRaster(raster_sintetico) as provedor:
        (cota,) = provedor.cotas_em([ponto])
    assert 600.0 <= cota <= 700.0


def test_cotas_seguem_a_ordem_dos_pontos(raster_sintetico):
    ponto = local_para_ponto(BAMBUI)
    deslocado = Ponto(x=ponto.x + 500.0, y=ponto.y)
    with ProvedorElevacaoRaster(raster_sintetico) as provedor:
        cotas = provedor.cotas_em([ponto, deslocado])
    assert len(cotas) == 2
    assert cotas[1] > cotas[0]


def test_ponto_fora_da_cobertura_levanta_erro(raster_sintetico):
    distance = Ponto(x=0.0, y=0.0)
    with (
        ProvedorElevacaoRaster(raster_sintetico) as provedor,
        pytest.raises(ElevacaoIndisponivelError, match="fora da cobertura"),
    ):
        provedor.cotas_em([distance])


def test_arquivo_inexistente_e_recusado(tmp_path):
    with pytest.raises(FileNotFoundError, match="não encontrado"):
        ProvedorElevacaoRaster(tmp_path / "ausente.tif")


def test_lote_vazio_devolve_tupla_vazia(raster_sintetico):
    with ProvedorElevacaoRaster(raster_sintetico) as provedor:
        assert provedor.cotas_em([]) == ()
