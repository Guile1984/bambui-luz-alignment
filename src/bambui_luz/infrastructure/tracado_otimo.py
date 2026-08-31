"""Geração de traçados por caminho de menor custo sobre grade.

O resultado é uma sequência de células adjacentes, com passos limitados ao
tamanho da célula e a oito direções. Representa um corredor de estudo, não
um eixo geométrico: a definição de geometria horizontal está fora do escopo
deste anteprojeto.
"""

import numpy as np
from skimage.graph import route_through_array


def caminho_de_menor_custo(
    custo: np.ndarray,
    origem: tuple[int, int],
    destino: tuple[int, int],
) -> tuple[list[tuple[int, int]], float]:
    """Encontra o caminho de menor custo acumulado entre duas células.

    Usa conectividade de oito vizinhos com ponderação geométrica: sem ela,
    movimentos diagonais cobririam mais terreno pelo mesmo custo e seriam
    artificialmente preferidos.

    Args:
        custo: Grade de custos de atravessamento, sem valores negativos.
        origem: Célula inicial, como (linha, coluna).
        destino: Célula final, como (linha, coluna).

    Returns:
        Lista de células percorridas, da origem ao destino, e o custo
        acumulado do percurso.

    Raises:
        ValueError: Se alguma célula estiver fora da grade ou se a grade
            contiver custos negativos ou indeterminados.
    """
    if np.isnan(custo).any():
        raise ValueError("a grade de custo não pode conter valores indeterminados")
    if (custo < 0).any():
        raise ValueError("a grade de custo não pode conter valores negativos")

    linhas, colunas = custo.shape
    for nome, celula in (("origem", origem), ("destino", destino)):
        linha, coluna = celula
        if not (0 <= linha < linhas and 0 <= coluna < colunas):
            raise ValueError(f"{nome} fora da grade de {linhas}x{colunas}: {celula}")

    caminho, custo_total = route_through_array(
        custo, origem, destino, fully_connected=True, geometric=True
    )
    return [tuple(celula) for celula in caminho], float(custo_total)
