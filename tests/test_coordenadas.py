"""Testes da fronteira de conversão de coordenadas."""

import pytest
from pyproj import Geod

from bambui_luz.config.estudo import BAMBUI, ESTEIOS, LUZ
from bambui_luz.infrastructure.coordenadas import (
    criar_transformador,
    exigir_crs_metrico,
    local_para_ponto,
)


def test_conversao_devolve_coordenadas_metricas():
    ponto = local_para_ponto(BAMBUI)
    assert 100_000 < ponto.x < 900_000
    assert 7_000_000 < ponto.y < 8_000_000


def test_conversao_nao_transfere_altitude_para_a_cota():
    assert local_para_ponto(BAMBUI).cota is None


def test_ordem_dos_eixos_preserva_leste_oeste():
    """Esteios está a leste de Bambuí; seu Este deve ser maior."""
    assert ESTEIOS.longitude_graus > BAMBUI.longitude_graus
    assert local_para_ponto(ESTEIOS).x > local_para_ponto(BAMBUI).x


def test_ordem_dos_eixos_preserva_norte_sul():
    """Luz está ao norte de Esteios; seu Norte deve ser maior."""
    assert LUZ.latitude_graus > ESTEIOS.latitude_graus
    assert local_para_ponto(LUZ).y > local_para_ponto(ESTEIOS).y


def test_crs_geografico_nao_serve_como_sistema_de_trabalho():
    with pytest.raises(ValueError, match="projetado"):
        exigir_crs_metrico("EPSG:4326")


def test_crs_de_trabalho_do_estudo_e_metrico():
    """A validação ocorre na importação; aqui confirmamos explicitamente."""
    from bambui_luz.config.estudo import CRS_TRABALHO

    assert exigir_crs_metrico(CRS_TRABALHO).is_projected


def test_transformador_aceita_destino_geografico():
    """Consultar um raster exige converter do sistema de trabalho para o dele."""
    transformador = criar_transformador("EPSG:31983", "EPSG:4326")
    longitude, latitude = transformador.transform(397802.68, 7787224.59)
    assert -46.5 < longitude < -45.5
    assert -20.5 < latitude < -19.5


def test_transformador_e_memorizado():
    primeiro = criar_transformador("EPSG:4674", "EPSG:31983")
    segundo = criar_transformador("EPSG:4674", "EPSG:31983")
    assert primeiro is segundo


@pytest.mark.parametrize(
    ("origem", "destino"), [(BAMBUI, ESTEIOS), (ESTEIOS, LUZ), (BAMBUI, LUZ)]
)
def test_distancia_projetada_confere_com_a_geodesica(origem, destino):
    """A distância em UTM deve concordar com a geodésica em até 0,1%."""
    geodesico = Geod(ellps="GRS80")
    _, _, distancia_geodesica = geodesico.inv(
        origem.longitude_graus,
        origem.latitude_graus,
        destino.longitude_graus,
        destino.latitude_graus,
    )
    distancia_projetada = local_para_ponto(origem).distancia_ate(
        local_para_ponto(destino)
    )
    assert distancia_projetada == pytest.approx(distancia_geodesica, rel=0.001)
