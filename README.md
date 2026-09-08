# bambui-luz-alignment

[![CI](https://github.com/Guile1984/bambui-luz-alignment/actions/workflows/ci.yml/badge.svg)](https://github.com/Guile1984/bambui-luz-alignment/actions/workflows/ci.yml)

Estudo comparativo de alternativas de traçado rodoviário entre Bambuí e o
distrito de Esteios, no Centro-Oeste de Minas Gerais.

## O problema

A ligação entre Bambuí e Luz passa pelo distrito de Esteios. O trecho
Esteios–Luz é pavimentado; o trecho **Bambuí–Esteios permanece em leito
natural**, com cerca de 28 km sem pavimentação, e é o objeto deste estudo.

A via é de jurisdição estadual, sob o DER-MG, e recebeu obras de
recuperação após mais de duas décadas sem manutenção. A pavimentação
permanece como expectativa, não como obra contratada.

**A pergunta do estudo:** existe traçado topograficamente melhor que o
atual entre Bambuí e Esteios?

## Resultado

**Não sob os critérios adotados.** O traçado existente é competitivo com o
melhor caminho gerado por otimização sobre modelo digital de elevação.

| Métrica | Traçado existente | Alternativa gerada | Variação |
|---|---:|---:|---:|
| Extensão | 37,30 km | 41,65 km | +11,7% |
| Relevo vencido | 1.046 m | 1.107 m | +5,8% |
| Extensão fora da classe | 4,40 km | 3,45 km | −21,5% |
| Volume movimentado | 2.929.926 m³ | 3.063.176 m³ | +4,5% |
| Rampa máxima do greide | 4,78% | 5,53% | — |
| Segmentos fora da classe | 0 de 374 | 0 de 417 | — |

O traçado existente vence em extensão, relevo vencido e volume de
terraplenagem. A alternativa vence apenas na extensão de trecho cujo
terreno excede a rampa da classe adotada — vantagem que não compensa
4,35 km adicionais e 133 mil m³ a mais de movimentação.

**Ambos admitem greide conforme à Classe III**, com rampas máximas de
4,78% e 5,53% contra o limite de 6,0%. A declividade natural de até 13,9%
não é impedimento: um greide adequado a resolve, ao custo da terraplenagem
quantificada acima.

**Nenhum dos dois é compensado.** Ambos exigiriam empréstimo de jazida —
472 mil m³ no existente e 661 mil m³ na alternativa.

### Interpretação

O traçado atual segue os divisores de água, com posição topográfica
mediana de +5,6 m em relação ao entorno de 450 m. É o princípio que
orienta estradas rurais desde antes de qualquer algoritmo: seguir a
cumeada evita travessias de curso d'água, favorece a drenagem e reduz a
manutenção.

O estudo indica que **não há razão topográfica evidente para deslocar o
eixo** em um eventual projeto de pavimentação.

## Revisões de premissa

O estudo partiu de informações que a apuração corrigiu. Cada revisão está
registrada com o que foi encontrado e como.

| Premissa inicial | O que a apuração mostrou | Como |
|---|---|---|
| Esteios é distrito de Bambuí | É vila do município de **Luz** | Cadastro de Localidades Selecionadas do IBGE |
| ~25 km em linha reta entre as cidades | **39,05 km** entre as sedes | Coordenadas do IBGE, verificadas por distância geodésica e projetada |
| ~70 km pelo percurso pavimentado atual | ~63 km pela BR-262 | Verificação independente por serviço de rotas |
| ~22 km de leito natural | **27,97 km** | Medição sobre a geometria do OpenStreetMap; refutado antes disso por geometria — a linha reta Bambuí–Esteios é de 30,22 km, e nenhum traçado pode ser menor que ela |
| Obra de pavimentação anunciada | Obra de **recuperação** do leito natural; pavimentação em fase de expectativa | Comunicação oficial da Prefeitura de Luz |

Uma quinta revisão ocorreu dentro do próprio estudo, e está descrita na
seção de método: a primeira alternativa gerada percorria o fundo de vale
por defeito do modelo de custo, o que invalidou uma conclusão preliminar
favorável a ela.

## Limitações técnicas

Esta seção é parte central do trabalho, não uma ressalva.

### 1. Natureza do estudo

Este é um **anteprojeto** — estudo comparativo preliminar de alternativas.
Não constitui projeto de engenharia, e as decisões que suporta são de
posição geral de corredor, não de definição de eixo.

### 2. Resolução do modelo de elevação

O Copernicus DEM GLO-30 tem células de aproximadamente 30 m. Duas
consequências medidas:

**A amostragem não pode ser mais fina que o dado.** Perfis extraídos a cada
20 m produziram rampa máxima de 35,26%, valor que nenhuma via trafegável
apresenta. A 100 m, a rampa cai para 13,87%, e a queda é monotônica sem
estabilização — assinatura de ruído, não de relevo. O estudo adota passo de
100 m por essa razão.

**Vales estreitos não são alcançados.** Uma célula de 30 m sobre um
talvegue inclui as encostas, de modo que a profundidade dos vales é
subestimada e o volume de aterro nas travessias, também.

### 3. Modelo de superfície, não de terreno

O Copernicus DEM é um **modelo digital de superfície**: representa o topo
do que existe no terreno, incluindo vegetação e edificações. Em pastagem a
diferença é de decímetros; em mata ciliar pode superar dez metros — e mata
ciliar ocorre justamente nos vales, onde o dado já é mais fraco.

O efeito superestima o volume de corte, em direção oposta ao da limitação
anterior. **Os dois erros não se cancelam de forma controlada.**

### 4. Greide simplificado

O greide é gerado por média móvel do terreno, sem otimização, sem curvas
verticais e sem ajuste local. A janela de 1.500 m foi escolhida como a
menor que produz greide conforme à classe adotada em ambos os traçados.

**Os volumes variam por um fator de dez ao longo da faixa de janelas
examinada** — de 359 mil m³ de corte com janela de 500 m a 3,83 milhões com
6.000 m, no mesmo traçado. Como a mesma janela se aplica às duas
alternativas, a comparação relativa se sustenta; **o valor absoluto não é
defensável.**

### 5. Seção transversal sobre terreno horizontal

A área de cada seção é calculada supondo terreno transversalmente
horizontal, o que subestima a área real em encosta, onde o talude do lado
superior é mais alto. A declividade mediana do corredor é de 9,6%, e nas
encostas acima de 20% a subestimativa é relevante.

### 6. O corredor não é um eixo

O traçado gerado avança por células de 30 m em oito direções possíveis. É
um **corredor de estudo**, não geometria horizontal: não há raios de curva,
superelevação nem transições.

### 7. Critérios ausentes do modelo

A superfície de custo considera declividade e posição topográfica. **Não
considera** uso do solo, propriedades, desapropriação, travessias de curso
d'água, áreas de preservação permanente, povoados ou demanda de tráfego.
Um traçado favorável neste estudo pode ser inviável por qualquer um desses
motivos.

### 8. Parâmetros normativos parcialmente verificados

A tabela de rampas máximas é atribuída ao Manual de Projeto Geométrico de
Rodovias Rurais (DNER, 1999). A vigência do manual e a existência da tabela
foram confirmadas em documentos oficiais derivados; **os valores numéricos
não foram lidos na fonte primária.**

### 9. Ponto de conexão em Esteios

O estudo adota a sede da vila como extremidade. O nó correto da rede é o
**entroncamento MG-429/MG-176**, que a rota real tangencia sem entrar na
vila. O trecho final do traçado gerado seria diferente com o destino
correto.

### 10. Fora de escopo

Geometria horizontal detalhada, drenagem, pavimento, obras de arte
especiais, desapropriação e orçamento financeiro.

## Finalidade

Trabalho **acadêmico e de portfólio**. Não constitui proposta de trabalho,
consultoria ou parecer técnico, e não guarda qualquer relação com processos
oficiais do Governo de Minas Gerais ou do DER-MG.

## Método

### Arquitetura

O código separa as regras de engenharia da tecnologia geoespacial, em seis
camadas:

| Camada | Responsabilidade |
|---|---|
| `domain` | Traçado, perfil, greide, rampas e volumes. Python puro, sem leitura de arquivo nem bibliotecas geoespaciais |
| `ports` | Contratos de acesso a dados externos |
| `infrastructure` | Rasterio, pyproj, OpenStreetMap, aquisição e conversão de coordenadas |
| `services` | Casos de uso: extração de perfil, comparação, relatório |
| `presentation` | Gráficos e mapas |
| `config` | Parâmetros e premissas do estudo, com procedência declarada |

A separação permite que toda a suíte de testes rode **sem os 79 MB de dados
reais** — o serviço de extração de perfil não sabe se conversa com um raster
ou com uma fonte de elevação sintética de três linhas.

### Sequência do estudo

1. Aquisição de dois tiles do Copernicus DEM, unidos e recortados ao corredor
2. Aferição do modelo contra altitudes oficiais do IBGE
3. Extração da malha viária do OpenStreetMap e montagem do grafo
4. Identificação do traçado existente por caminho mínimo no grafo
5. Composição da superfície de custo e geração da alternativa
6. Extração dos perfis, definição dos greides e cálculo dos volumes
7. Comparação e análise de sensibilidade aos parâmetros

### Verificações independentes

Cada resultado foi confrontado com uma medida que não participou de sua
produção:

**Aferição do modelo de elevação.** As cotas lidas nas três localidades
diferem das altitudes do IBGE em −3,3 m, −5,0 m e +2,4 m. A maior diferença
absoluta é de 5,0 m e os sinais alternam, o que indica ruído aleatório e não
deslocamento sistemático de referência vertical. Isso valida, de uma vez, a
leitura de coordenadas, a projeção, a conversão ao sistema do raster e a
interpolação.

**Distâncias por dois métodos.** As distâncias projetadas em UTM concordam
com as geodésicas dentro de 0,03% — trezentas vezes menor que uma célula do
modelo de elevação.

**Limite inferior geométrico.** Nenhum traçado pode ser menor que a linha
reta entre seus extremos. Os 30,22 km entre Bambuí e Esteios refutaram uma
extensão de 22 km atribuída ao trecho de terra antes de qualquer medição.

### Análise de sensibilidade

Os pesos da superfície de custo são arbitrados. Uma varredura de quinze
combinações verificou se as conclusões dependem deles.

Com penalidade de talvegue igual ou superior a 3, todas as combinações
produzem o mesmo corredor: posição topográfica mediana entre +10,7 e
+13,0 m, com sobreposição de 73% a 100% das células. Os dois pesos competem
— quanto maior a penalidade de declividade, mais atraente fica o vale, que
é a região mais plana, e mais penalidade de talvegue é necessária para
escapar dele.

### Correção de modelo durante o estudo

A primeira versão da superfície de custo penalizava apenas a declividade do
terreno. O traçado gerado apresentou, nessa versão, desempenho superior ao
existente em todas as métricas — 47,7% menos relevo vencido e 67,9% menos
volume movimentado.

A inspeção do perfil revelou forma incompatível com o relevo da região: o
traçado descia continuamente a 635 m e subia 70 m nos quilômetros finais.
A investigação confirmou que ele **percorria o fundo de vale**: cota mediana
de 647,4 m contra 717,9 m do existente, com 87,3% dos pontos abaixo do
terreno vizinho.

A causa é conceitual. Em relevo ondulado há dois lugares planos — o topo
dos divisores e o fundo dos vales — e o vale é mais direto. Uma função de
custo baseada só em declividade não os distingue, e ignora os custos de
drenagem, travessia, inundação e restrição ambiental que o vale acarreta.

A correção acrescentou ao custo o **índice de posição topográfica**, com
penalidade quadrática aplicada apenas às células rebaixadas em relação ao
entorno. A assimetria é deliberada: penalizar os dois sentidos empurraria o
traçado à meia encosta, que é a pior posição.

Com o modelo corrigido, a alternativa passou a percorrer divisores — posição
mediana de +13,0 m — e a conclusão do estudo se inverteu.

**A análise de sensibilidade não havia detectado o defeito.** Ela verifica se
o resultado depende dos parâmetros, não se o modelo representa a realidade.
Os traçados eram robustos aos pesos, e todos percorriam o vale.

## Reprodução

O ambiente exige conda: as bibliotecas geoespaciais têm dependências
binárias que o pip não resolve de forma confiável no Windows.

```bash
conda env create -f environment.yml
conda activate bambui-luz
pip install -e . --no-deps
pre-commit install
```

Execução completa do estudo, do download à figura final:

```bash
python notebooks/reproduzir_estudo.py
```

São doze etapas, com download de aproximadamente 79 MB na primeira
execução. Os downloads são idempotentes: arquivos já presentes não são
rebaixados.

Verificações locais:

```bash
ruff check .
pytest
```

## Estrutura do repositório

```
src/bambui_luz/     código-fonte, em seis camadas
tests/              suíte de testes, sem dependência de dados reais
notebooks/          scripts de execução e exploração
data/raw/           dados originais, não versionados
data/processed/     dados derivados, não versionados
docs/               documentação
NOTES.md            decisões, trade-offs e pendências
```

## Fontes de dados

**Modelo digital de elevação** — Copernicus DEM GLO-30, obtido do
repositório público em nuvem. Produzido a partir de dados adquiridos pela
missão TanDEM-X entre 2011 e 2015.

> © DLR e.V. (2010–2014) e © Airbus Defence and Space GmbH (2014–2018),
> fornecidos sob COPERNICUS pela União Europeia e pela ESA; todos os
> direitos reservados.

**Malha viária** — OpenStreetMap, obtida pela API Overpass.

> © colaboradores do OpenStreetMap, disponibilizado sob Open Database
> License (ODbL).

Geometrias derivadas do OpenStreetMap **não são versionadas** neste
repositório: a ODbL impõe compartilhamento nos mesmos termos a bases
derivadas, e o código permanece sob licença MIT. Os arquivos são
reconstruídos pelos scripts de aquisição.

**Localidades de referência** — IBGE, Cadastro de Localidades Selecionadas
2010.

## Licença

Código sob licença MIT. Ver `LICENSE`.
