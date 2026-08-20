"""Testes dos parâmetros normativos de projeto geométrico."""

import pytest

from bambui_luz.domain.rodovia import ClasseRodovia

FONTE_EXEMPLO = "valor de exemplo, sem vínculo normativo"


def _classe(rampa_maxima_pct: float = 5.0) -> ClasseRodovia:
    return ClasseRodovia(
        nome="classe de teste",
        velocidade_diretriz_kmh=80.0,
        rampa_maxima_pct=rampa_maxima_pct,
        fonte=FONTE_EXEMPLO,
    )


def test_rampa_abaixo_do_limite_e_admissivel():
    assert _classe().rampa_admissivel(3.2) is True


def test_rampa_acima_do_limite_e_rejeitada():
    assert _classe().rampa_admissivel(7.5) is False


def test_limite_e_inclusivo():
    assert _classe(rampa_maxima_pct=5.0).rampa_admissivel(5.0) is True


def test_declive_e_avaliado_pelo_valor_absoluto():
    classe = _classe(rampa_maxima_pct=5.0)
    assert classe.rampa_admissivel(-4.0) is True
    assert classe.rampa_admissivel(-6.0) is False


def test_classe_exige_fonte_declarada():
    with pytest.raises(ValueError, match="fonte"):
        ClasseRodovia(
            nome="sem fonte",
            velocidade_diretriz_kmh=80.0,
            rampa_maxima_pct=5.0,
            fonte="     ",
        )


def test_classe_rejeita_rampa_maima_implausivel():
    with pytest.raises(ValueError, match="plausível"):
        ClasseRodovia(
            nome="implausível",
            velocidade_diretriz_kmh=80.0,
            rampa_maxima_pct=45.0,
            fonte=FONTE_EXEMPLO,
        )


def test_classe_rejeita_velocidade_nao_positiva():
    with pytest.raises(ValueError, match="velocidade"):
        ClasseRodovia(
            nome="parada",
            velocidade_diretriz_kmh=0.0,
            rampa_maxima_pct=5.0,
            fonte=FONTE_EXEMPLO,
        )
