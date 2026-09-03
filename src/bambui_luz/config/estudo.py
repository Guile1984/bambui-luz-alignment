"""Parâmetros e premissas do estudo.

As coordenadas são armazenadas em graus decimais, na forma em que a fonte
as publica. A conversão para o sistema métrico de trabalho é atribuição da
camada de infraestrutura.
"""

from dataclasses import dataclass

from bambui_luz.domain.rodovia import ClasseRodovia

CRS_GEOGRAFICO = "EPSG:4674"
"""SIRGAS 2000 geográfico, em graus decimais. Forma de publicação do IBGE."""

CRS_TRABALHO = "EPSG:31983"
"""SIRGAS 2000 / UTM zona 23S, em metros. Sistema de cálculo do estudo."""


@dataclass(frozen=True, slots=True)
class LocalNotavel:
    """Localidade de referência do estudo, como publicada pela fonte.

    Não confundir com Ponto, do domínio: este tipo guarda coordenadas
    geográficas em graus e sua procedência enquanto Ponto opera em metros
    e desconhece a origem do dado.

    Attributes:
        nome: Identificação da localidade.
        latitude_graus: Latitude em graus decimais, negativa ao sul.
        longitude_graus: Longitude em graus decimais, negativa a oeste.
        fonte: Procedência do par de coordenadas. Campo obrigatório.
        altitude_ibge_m: Altitude publicada pela fonte, em metros, quando
            disponível. Usada como aferiação independente do modelo digital
            de elevação, não como dado de cálculo.
    """

    nome: str
    latitude_graus: float
    longitude_graus: float
    fonte: str
    altitude_ibge_m: float | None = None

    def __post_init__(self) -> None:
        """Valida a localidade na construção.

        Raises:
            ValueError: Se o nome ou a fonte estiverem vazios, ou se as
                coordenadas estiverem fora da faixa geográfica válida.
        """
        if not self.nome.strip():
            raise ValueError("a localidade exige um nome não vazio")
        if not self.fonte.strip():
            raise ValueError(
                f"a localidade '{self.nome}' exige a declaração da fonte "
                "das coordenadas"
            )
        if not -90.0 <= self.latitude_graus <= 90.0:
            raise ValueError(
                f"latitude fora da faixa válida em '{self.nome}': {self.latitude_graus}"
            )
        if not -180.0 <= self.longitude_graus <= 180.0:
            raise ValueError(
                f"longitude fora da faixa válida em '{self.nome}': "
                f"{self.longitude_graus}"
            )


FONTE_IBGE = (
    "IBGE, Cadastro de Localidades Selecionadas 2010, "
    "BR_Localidades_2010_v1, consultado em 2026-08-24"
)
"""Procedência das coordenadas das localidades de referência."""

BAMBUI = LocalNotavel(
    nome="Bambuí",
    latitude_graus=-20.011892,
    longitude_graus=-45.979045,
    fonte=FONTE_IBGE,
    altitude_ibge_m=684.938671,
)
"""Sede do município de Bambuí, categoria CIDADE."""

ESTEIOS = LocalNotavel(
    nome="Esteios",
    latitude_graus=-19.928235,
    longitude_graus=-45.704223,
    fonte=FONTE_IBGE,
    altitude_ibge_m=692.065772,
)
"""Sede da vila de Esteios, no município de Luz. Ponto de conexão com a
malha pavimentada existente."""

LUZ = LocalNotavel(
    nome="Luz",
    latitude_graus=-19.796247,
    longitude_graus=-45.683881,
    fonte=FONTE_IBGE,
    altitude_ibge_m=663.733692,
)
"""Sede do município de Luz, categoria CIDADE."""

MARGEM_CORREDOR_M = 5000.0
"""Folga aplicada em torno das localidades ao recortar o modelo de elevação.

Dimensionada para acomodar traçados alternativos que se afastem da linha
reta entre os extremos. Um traçado que alcance a borda do recorte indica
margem insuficiente, não defeito do algoritmo.
"""

DECLIVIDADE_REFERENCIA_PCT = 10.0
"""Declividade de referência para normalizar a penalidade de custo.

Serve para tornar o peso interpretável: ele expressa quanto custa a mais
atravessar uma encosta desta declividade em relação a terreno plano.
"""

PESO_DECLIVIDADE = 4.0
"""Peso da penalidade por declividade na superfície de custo.

VALOR ARBITRADO, não normativo. Significa que atravessar uma encosta de
10% custa cinco vezes o custo de terreno plano.

A análise de sensibilidade (pesos 0 a 16) mostrou que a partir do peso 2 o
corredor escolhido é ditado pelo terreno: os pesos 4, 8 e 16 compartilham
100% das células. Este valor cai dentro desse patamar estável.
"""

DECLIVIDADE_BARREIRA_PCT = 25.0
"""Declividade acima da qual a travessia recebe custo proibitivo.

VALOR ARBITRADO. Corresponde a terreno onde a implantação exigiria obras
de contenção fora do escopo deste anteprojeto.
"""

CUSTO_BARREIRA = 1000.0
"""Custo atribuído a células acima da declividade de barreira.

Alto o bastante para desencorajar a travessia, finito para que o algoritmo
encontre solução quando não houver alternativa, em vez de falhar.
"""

FONTE_DNER_1999 = (
    "Tabela de rampas máximas atribuída ao Manual de Projeto Geométrico de "
    "Rodovias Rurais (DNER, 1999, p. 124). PARCIALMENTE VERIFICADA: a "
    "vigência do manual e a existência da tabela foram confirmadas em "
    "documentos oficiais derivados (DER-SP, GOINFRA, DER-MG), mas os valores "
    "numéricos não foram lidos na fonte primária. Consultado em 2026-09-02."
)
"""Procedência dos parâmetros normativos, com o estado da verificação."""

CLASSE_ADOTADA = ClasseRodovia(
    nome="Classe III — relevo ondulado",
    velocidade_diretriz_kmh=60.0,
    rampa_maxima_pct=6.0,
    fonte=FONTE_DNER_1999,
)
"""Classe de projeto adotada no estudo.

Hipótese de trabalho: ligação vicinal entre polos agropecuários, em relevo
cuja declividade mediana medida no corredor é de 9,6%. A escolha da classe
é premissa do estudo, não determinação normativa, e altera diretamente a
extensão de traçado considerada inadmissível.
"""

LARGURA_PLATAFORMA_M = 10.0
"""Largura da plataforma adotada, em metros.

VALOR ARBITRADO. Corresponde a duas faixas de rolamento de 3,5 m e
acostamentos de 1,5 m, compatível com a classe de projeto adotada. Não
inclui alargamento em curva, fora do escopo deste anteprojeto.
"""

TALUDE_CORTE_H_V = 1.0
"""Inclinação do talude de corte, em metros horizontais por metro vertical.

VALOR ARBITRADO. Prática usual em solo, sem sondagem geotécnica que
justifique valor específico.
"""

TALUDE_ATERRO_H_V = 1.5
"""Inclinação do talude de aterro, em metros horizontais por metro vertical.

VALOR ARBITRADO. Mais suave que o de corte porque o material recompactado
tem menor coesão que o solo natural. Implica maior área de seção para a
mesma altura, de modo que aterro custa mais volume que corte equivalente.
"""

FATOR_CONVERSAO_CORTE_ATERRO = 0.90
"""Volume de aterro compactado obtido por metro cúbico de corte no maciço.

VALOR ARBITRADO, sem sondagem. Combina empolamento na escavação e
contração na compactação. Serve para avaliar compensação em ordem de
grandeza, não para dimensionamento.
"""

JANELA_SUAVIZACAO_GREIDE_M = 1500.0
"""Largura da janela de média móvel usada para gerar o greide, em metros.

VALOR ARBITRADO. Janelas curtas fazem o greide copiar o terreno e não
reduzem rampas; janelas longas o descolam do solo e inflam os volumes de
terraplenagem. A sensibilidade a este valor é objeto de análise própria.
"""
