"""Conversão de coordenadas geográficas para o sistema métrico de trabalho.

Este módulo é a fronteira onde graus se tornam metros. Nenhuma coordenada
em graus atravessa para o domínio: a validação do sistema de destino é
executada em tempo de execução, e não apenas presumida.
"""

from functools import cache

from pyproj import CRS, Transformer

from bambui_luz.config.estudo import CRS_GEOGRAFICO, CRS_TRABALHO, LocalNotavel
from bambui_luz.domain.geometria import Ponto

UNIDADE_METRICA = "metre"
"""Nome da unidade de eixo exigida no sistema de referência de trabalho."""


def exigir_crs_metrico(codigo: str) -> CRS:
    """Valida que o sistema de referência é projetado e expresso em metros.

    Args:
        codigo: Identificador do sistema de referência, como "EPSG:31983".

    Returns:
        Sistema de referência validado.
    """
    crs = CRS.from_user_input(codigo)
    if not crs.is_projected:
        raise ValueError(
            f"o sistema de trabalho deve ser projetado, não geográfico: {codigo}"
        )
    unidades = {eixo.unit_name for eixo in crs.axis_info}
    if unidades != {UNIDADE_METRICA}:
        raise ValueError(
            f"o sistema de trabalho deve ser todos os eixos em metros; "
            f"encontrado em {codigo}: {sorted(unidades)}"
        )
    return crs


CRS_TRABALHO_VALIDADO = exigir_crs_metrico(CRS_TRABALHO)
"""Sistema de trabalho, validado como projetado e métrico ao importar o módulo.

A verificação ocorre uma única vez, na importação: trocar o sistema de
trabalho por um geográfico faz o pacote falhar imediatamente, em vez de
produzir distâncias em graus silenciosamente.
"""


@cache
def criar_transformador(crs_origem: str, crs_destino: str) -> Transformer:
    """Constrói um transformador entre dois sistemas de referênia.

    O resultado é memorizado: chamadas repetidas com os mesmo argumentos
    reaproveitam o mesmo objeto, evitando o custo de reconstrução.

    Args:
        crs_origem: Sistema de referência de origem.
        crs_destino: Sistema de referência de destino, obrigatoriamente
            projetado e em metros.

    Returns:
        Transformador configurado na ordem de eixos x, y.
    """
    return Transformer.from_crs(crs_origem, crs_destino, always_xy=True)


def local_para_ponto(local: LocalNotavel) -> Ponto:
    """Converte uma localidade de referência em ponto métrico do domínio.

    A altitude publicada pela fonte não é transferida para a cota: ela serve
    à aferição independente do modelo digital de elevação, e mistrurá-lo ao
    dado de cálculo anularia essa independência.

    Args:
        local: Localidade com coordenadas em graus decimais.

    Returns:
        Ponto em coordenadas métricas projetadas, sem cota definida.
    """
    transformador = criar_transformador(CRS_GEOGRAFICO, CRS_TRABALHO)
    x, y = transformador.transform(local.longitude_graus, local.latitude_graus)
    return Ponto(x=x, y=y)
