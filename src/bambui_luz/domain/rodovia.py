"""Parâmetros normativos de projeto geométrico rodoviário.

Esta camada não define quais são os valores da norma: ela define como
utilizá-los. Os valores concretos, com sua procedência, pertencem à
camada de configuração do estudo.
"""

from dataclasses import dataclass

RAMPA_MAXIMA_PLAUSIVEL_PCT = 20.0
"""Limite superior de sanidade para rampa máxima admissível, em porcentagem"""


@dataclass(frozen=True, slots=True)
class ClasseRodovia:
    """Parâmetros de projeto de uma classe de rodovia em um dado relevo.

    A rampa máxima admissível depende conjuntamente da classe de projeto e
    do tipo de relevo atravessado, razão pela qual ambos são fixados nesta
    entidade em vez de tratados separadamente.

    Attributes:
        nome: Identificação da classe e do relevo, para relatórios.
        velocidade_diretriz_kmh: Velocidade diretriz adotada, em km/h.
        rampa_maxima_pct: Rampa máxima admissível, em porcentagem, aplicável
            tanto a aclives quanto a declives.
        fonte: Referência bibliográfica de onde os valores foram obtidos.
            Campo obrigatório: parâmetro normativo em procedência declarada
            não é utilizável em estudo de engenharia.
    """

    nome: str
    velocidade_diretriz_kmh: float
    rampa_maxima_pct: float
    fonte: str

    def __post_init__(self) -> None:
        """Valida os parâmetros normativos na construção.

        Raises:
            ValueError: Se algum parâmetro estiver fora de faixa plausível
                ou se a fonte não tiver sido declarada.
        """
        if not self.nome.strip():
            raise ValueError("a classe de rodovia exige um nome não vazio")
        if not self.fonte.strip():
            raise ValueError(
                f"a classe '{self.nome}' exige a declaração da fonte dos parâmetros"
            )
        if self.velocidade_diretriz_kmh <= 0:
            raise ValueError(
                f"velocidade diretriz deve ser positiva: {self.velocidade_diretriz_kmh}"
            )
        if not 0 < self.rampa_maxima_pct <= RAMPA_MAXIMA_PLAUSIVEL_PCT:
            raise ValueError(
                f"rampa máxima fora da faixa plausível "
                f"(0, {RAMPA_MAXIMA_PLAUSIVEL_PCT}]: {self.rampa_maxima_pct})"
            )

    def rampa_admissivel(self, rampa_pct: float) -> bool:
        """Informa se uma rampa atende ao limite da classe.

        O sinal é desconsiderado: o limite normativo aplica-se igualmente a
        aclives e declives.

        Args:
            rampa_pct: Rampa a verificar, em porcentagem. Positiva em
                aclive, negativa em declive.

        Returns:
            True se a rampa for admissível para esta classe.
        """
        return abs(rampa_pct) <= self.rampa_maxima_pct
