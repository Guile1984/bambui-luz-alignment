"""Verifica a integridade estrutural do pacote instalado."""

import importlib

import pytest

CAMADAS = [
    "bambui_luz.config",
    "bambui_luz.domain",
    "bambui_luz.infrastructure",
    "bambui_luz.ports",
    "bambui_luz.presentation",
    "bambui_luz.services",
]


def test_pacote_raiz_importavel() -> None:
    modulo = importlib.import_module("bambui_luz")
    assert modulo.__doc__, "o pacote raiz deve ter docstring"


@pytest.mark.parametrize("camada", CAMADAS)
def test_camada_importavel_e_documentada(camada: str) -> None:
    modulo = importlib.import_module(camada)
    assert modulo.__doc__, f"a camada {camada} deve ter docstring de pacote"
