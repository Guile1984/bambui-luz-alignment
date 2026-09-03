"""Geração e verificação do greide de projeto.

O greide é a linha em que a estrada efetivamente ficará, distinta do
perfil do terreno natural. Onde está abaixo do terreno há corte; onde está
acima, aterro.

O método adotado é a suavização por média móvel, e não a otimização do
greide: definir geometria vertical detalhada está fora do escopo deste
anteprojeto. As rampas resultantes são verificadas e relatadas, não
forçadas ao limite da classe.
"""

from dataclasses import dataclass
from itertools import pairwise

from bambui_luz.domain.perfil import PerfilLongitudinal, PontoPerfil
from bambui_luz.domain.rodovia import ClasseRodovia


@dataclass(frozen=True, slots=True)
class Greide:
    """Linha de projeto ao longo de um traçado.

    Attributes:
        estacoes: Estações do greide, com a cota de projeto em cada uma.
            Compartilham as distâncias do perfil do terreno que as
            originou.
    """

    estacoes: tuple[PontoPerfil, ...]

    def __post_init__(self) -> None:
        """Valida a estrutura do greide na construção.

        Raises:
            TypeError: Se as estações não forem fornecidas em uma tupla.
            ValueError: Se houver menos de duas estações.
        """
        if not isinstance(self.estacoes, tuple):
            raise TypeError(
                "as estações devem ser uma tupla, para garantir imutabilidade; "
                f"recebido: {type(self.estacoes).__name__}"
            )
        if len(self.estacoes) < 2:
            raise ValueError(
                f"um greide exige ao menos duas estações; "
                f"recebidas: {len(self.estacoes)}"
            )

    def __len__(self) -> int:
        """Retorna a quantidade de estações do greide."""
        return len(self.estacoes)

    def rampas(self) -> tuple[float, ...]:
        """Calcula a rampa de cada segmento do greide, em porcentagem.

        Returns:
            Rampas em porcentagem, positivas em aclive no sentido de
            percurso. Tem um elemento a menos que a quantidade de estações.
        """
        return tuple(
            (atual.cota_m - anterior.cota_m)
            / (atual.distancia_m - anterior.distancia_m)
            * 100.0
            for anterior, atual in pairwise(self.estacoes)
        )

    @property
    def rampa_maxima_absoluta(self) -> float:
        """Maior rampa do grede em valor absoluto, em porcentagem."""
        return max(abs(rampa) for rampa in self.rampas())

    def segmentos_inadmissiveis(self, classe: ClasseRodovia) -> tuple[int, ...]:
        """Localiza os segmentos do greide que excedem a classe adotada.

        A suavização reduz as rampas, mas não as limita: uma encosta longa
        e constante sobrevive a qualquer média móvel. Os excedentes são
        informação sobre a dificuldade do traçado.

        Args:
            classe: Classe de rodovia cujo limite será aplicado.

        Returns:
            Índices dos segmentos que excedem o limite.
        """
        return tuple(
            indice
            for indice, rampa in enumerate(self.rampas())
            if not classe.rampa_admissivel(rampa)
        )


def suavizar(perfil: PerfilLongitudinal, janela_m: float) -> Greide:
    """Gera o greide por média móvel das cotas do terreno.

    Nas extremidades a janela é reduzida aos pontos disponíveis, de modo
    que o greide se aproxima do terreno nos extremos - o que é adequado,
    já que a estrada precisa encontrar o terreno em suas pontas.

    Args:
        perfil: Perfil longitudinal do terreno natural.
        janela_m: Largura total da janela de suavização, em metros.

    Returns:
        Greide com as mesmas distâncias do perfil de origem.

    Raises:
        ValueError: Se a janela não for positiva.
    """
    if janela_m <= 0:
        raise ValueError(f"a janela de suavização deve ser positiva: {janela_m}")

    meia_janela = janela_m / 2
    suavizadas = []
    for estacao in perfil.estacoes:
        vizinhas = [
            outra.cota_m
            for outra in perfil.estacoes
            if abs(outra.distancia_m - estacao.distancia_m) <= meia_janela
        ]
        suavizadas.append(
            PontoPerfil(
                distancia_m=estacao.distancia_m,
                cota_m=sum(vizinhas) / len(vizinhas),
            )
        )
    return Greide(estacoes=tuple(suavizadas))
