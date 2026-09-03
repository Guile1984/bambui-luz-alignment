"""Testes dos parâmetros e premissas do estudo."""

import pytest

from bambui_luz.config.estudo import (
    BAMBUI,
    CRS_GEOGRAFICO,
    CRS_TRABALHO,
    ESTEIOS,
    LUZ,
    LocalNotavel,
)

FONTE_EXEMPLO = "coordenada fictícia, apenas para teste"


def test_crs_de_trabalho_e_metrico_utm_23s():
    assert CRS_TRABALHO == "EPSG:31983"


def test_crs_geografico_e_sirgas_2000():
    assert CRS_GEOGRAFICO == "EPSG:4674"


def test_local_armazena_coordenadas_em_graus():
    local = LocalNotavel(
        nome="local fictício",
        latitude_graus=-20.0,
        longitude_graus=-46.0,
        fonte=FONTE_EXEMPLO,
    )
    assert local.latitude_graus == pytest.approx(-20.0)
    assert local.longitude_graus == pytest.approx(-46.0)


def test_local_exige_fonte_declarada():
    with pytest.raises(ValueError, match="fonte"):
        LocalNotavel(
            nome="sem nome",
            latitude_graus=-20.0,
            longitude_graus=-46.0,
            fonte="  ",
        )


def test_local_rejeita_latitude_fora_da_faixa():
    with pytest.raises(ValueError, match="latitude"):
        LocalNotavel(
            nome="impossível",
            latitude_graus=-120.0,
            longitude_graus=-46.0,
            fonte=FONTE_EXEMPLO,
        )


def test_local_rejeita_longitude_fora_da_faixa():
    with pytest.raises(ValueError, match="longitude"):
        LocalNotavel(
            nome="impossível",
            latitude_graus=-20.0,
            longitude_graus=-200.0,
            fonte=FONTE_EXEMPLO,
        )


def test_localidades_de_referencia_tem_fonte_do_ibge():
    for local in (BAMBUI, ESTEIOS, LUZ):
        assert "IBGE" in local.fonte


def test_localidades_estao_no_centro_oeste_mineiro():
    for local in (BAMBUI, ESTEIOS, LUZ):
        assert -21.0 < local.latitude_graus < -19.0
        assert -47.0 < local.longitude_graus < -45.0


def test_localidades_estao_no_fuso_utm_23():
    for local in (BAMBUI, ESTEIOS, LUZ):
        assert -48.0 <= local.longitude_graus < -42.0


def test_altitudes_de_referencia_estao_registradas():
    for local in (BAMBUI, ESTEIOS, LUZ):
        assert local.altitude_ibge_m is not None
        assert 500.0 < local.altitude_ibge_m < 900.0


def test_local_aceita_altitude_ausente():
    local = LocalNotavel(
        nome="sem altitude",
        latitude_graus=-20.0,
        longitude_graus=-46.0,
        fonte=FONTE_EXEMPLO,
    )
    assert local.altitude_ibge_m is None


def test_parametros_de_secao_sao_fisicamente_plausiveis():
    from bambui_luz.config.estudo import (
        FATOR_CONVERSAO_CORTE_ATERRO,
        LARGURA_PLATAFORMA_M,
        TALUDE_ATERRO_H_V,
        TALUDE_CORTE_H_V,
    )

    assert 6.0 <= LARGURA_PLATAFORMA_M <= 20.0
    assert 0.5 <= TALUDE_CORTE_H_V <= 3.0
    assert 0.5 <= TALUDE_ATERRO_H_V <= 3.0
    assert TALUDE_ATERRO_H_V >= TALUDE_CORTE_H_V
    assert 0.7 <= FATOR_CONVERSAO_CORTE_ATERRO <= 1.0
