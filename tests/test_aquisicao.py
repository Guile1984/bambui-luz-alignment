"""Testes da lógica de identificação de tiles de elevação."""

from bambui_luz.config.estudo import BAMBUI, ESTEIOS, LUZ
from bambui_luz.infrastructure.aquisicao import nome_tile, tiles_necessarios, url_tile


def test_bambui_esta_no_tile_ao_sul_do_paralelo_de_20():
    """Bambuí está a 20,01 graus sul: o piso é -21, não -20."""
    nome = nome_tile(BAMBUI.latitude_graus, BAMBUI.longitude_graus)
    assert nome == "Copernicus_DSM_COG_10_S21_00_W046_00_DEM"


def test_esteios_e_luz_estao_no_tile_ao_norte():
    esperado = "Copernicus_DSM_COG_10_S20_00_W046_00_DEM"
    assert nome_tile(ESTEIOS.latitude_graus, ESTEIOS.longitude_graus) == esperado
    assert nome_tile(LUZ.latitude_graus, LUZ.longitude_graus) == esperado


def test_corredor_exige_dois_tiles():
    coordenadas = [
        (local.latitude_graus, local.longitude_graus)
        for local in (BAMBUI, ESTEIOS, LUZ)
    ]
    assert len(tiles_necessarios(coordenadas)) == 2


def test_hemisferio_norte_e_leste():
    assert nome_tile(20.5, 10.5) == "Copernicus_DSM_COG_10_N20_00_E010_00_DEM"


def test_grau_inteiro_pertence_ao_tile_que_ele_inicia():
    assert nome_tile(-20.0, -46.0) == "Copernicus_DSM_COG_10_S20_00_W046_00_DEM"


def test_url_repete_o_nome_como_pasta_e_arquivo():
    """O bucket organiza cada tile em uma pasta homônima."""
    nome = "Copernicus_DSM_COG_10_S21_00_W046_00_DEM"
    assert url_tile(nome).endswith(f"/{nome}/{nome}.tif")
