# NOTES

Registro de decisões, trade-offs e pendências do projeto.
Complementa o README, que descreve o que o sistema é e como usá-lo.

## Decisões com trade-off

### Dependências: environment.yml como fonte da verdade
O `environment.yml` declara as dependências; o `pyproject.toml` declara
apenas identidade e configuração de ferramentas. O pacote é instalado com
`pip install -e . --no-deps`.

**Motivo:** as bibliotecas geoespaciais (GDAL, rasterio, geopandas) têm
dependências binárias. Declará-las no `pyproject.toml` levaria o pip a
instalar wheels com cópias próprias da GDAL sobre o ambiente conda,
gerando conflito de bibliotecas compartilhadas.

**Custo aceito:** o `pyproject.toml` fica menos autossuficiente que o de um
projeto puro-Python. Quem clonar precisa do conda, não apenas do pip.

### Versões não fixadas, exceto o Python
Apenas `python=3.12` está travado no `environment.yml`.

**Motivo:** travar versões protege contra quebras futuras, mas impede
correções e complica a resolução no CI. Em desenvolvimento ativo, o custo
de manter pinos supera o risco.

**Gatilho de revisão:** gerar lockfile (`conda-lock`) se o projeto for
arquivado ou publicado como referência reproduzível.

### .gitignore explícito para data/
O bloco de `data/` usa reinclusão explícita de cada diretório em vez de
padrões com `**`.

**Motivo:** clareza e revisibilidade. A versão com `**` provavelmente
funcionava; a escolha foi por legibilidade, não por correção.

### .vscode/ ignorado por completo
**Motivo:** contém configuração pessoal de máquina, não de projeto.

**Gatilho de revisão:** se o projeto ganhar colaboradores, considerar
versionar seletivamente `.vscode/extensions.json`.

### Fins de linha geridos por .gitattributes
Política LF definida em `.gitattributes` (versionado), não em
`core.autocrlf` (configuração de máquina).

**Motivo:** a política viaja com o repositório e vale para qualquer sistema
operacional. `.gitattributes` tem precedência sobre `core.autocrlf`.

### CI em Linux, não em Windows
O workflow roda em `ubuntu-latest`, embora o desenvolvimento seja em Windows.

**Motivo:** a divergência de sistema operacional é o que revela problemas —
separadores de caminho, fins de linha, sensibilidade a maiúsculas. Um CI que
espelha a máquina de desenvolvimento não testa portabilidade.

**Gatilho de revisão:** se surgir defeito específico de Windows, considerar
matriz de sistemas operacionais no workflow.

### CI verifica, não corrige
O workflow usa `ruff format --check`, não `ruff format`.

**Motivo:** correção automática no servidor produziria divergência entre o
código enviado e o verificado, mascarando a ausência do hook local.

### Domínio em Python puro, sem NumPy
As entidades do domínio operam sobre tuplas e floats, sem bibliotecas
numéricas.

**Motivo:** manter a camada legível por um engenheiro civil, sem exigir
vocabulário de arrays. Os perfis têm poucos milhares de estações e os
cálculos são elementares.

**Gatilho de revisão:** se o desempenho se tornar limitante no cálculo de
volumes (Sprint 5), avaliar a vetorização apenas na camada de serviços.

### Parâmetros normativos fora do domínio
`ClasseRodovia` recebe a rampa máxima como dado, não a define. O campo
`fonte` é obrigatório e não pode ser vazio.

**Motivo:** norma é premissa do estudo, não regra do sistema. A
obrigatoriedade da fonte impede, pelo sistema de tipos, que um parâmetro
normativo sem procedência seja utilizado.

### Trecho em estudo: Bambuí a Esteios
O estudo concentra-se no trecho Bambuí–Esteios; Esteios passa a ser o ponto
de conexão com a malha pavimentada existente, e não waypoint intermediário.

**Motivo:** o trecho Esteios–Luz é reportado como pavimentado, restando
decisão de traçado apenas no segmento a oeste. Escopo menor e pergunta de
engenharia melhor posta.

**A verificar:** a pavimentação do trecho Esteios–Luz e a extensão exata do
leito natural, ambas mensuráveis na Sprint 3.

### Fonte de elevação: Copernicus GLO-30 Public
Tiles obtidos do bucket público em nuvem, sem credencial. Dois tiles cobrem
o corredor, pois ele cruza o paralelo de 20 graus sul.

**Motivo:** cobertura global a 30 m, formato COG, acesso livre e licença
gratuita. Verificado e baixado em 2026-08-25.

**Custo aceito:** é modelo de superfície (DSM), não de terreno — inclui
vegetação e edificações. Ver risco R10.

**Atribuição obrigatória:** a licença exige aviso creditando DLR, Airbus
Defence and Space, União Europeia e ESA. Transcrever o texto literal da
licença para o README antes da publicação final.

### Recorte permanece no CRS da fonte
O recorte do corredor não é reprojetado para UTM; a conversão acontece por
ponto, na consulta.

**Motivo:** reprojetar o raster reamostra todos os pixels, acrescentando uma
interpolação entre a fonte e o resultado — depois seria impossível separar o
erro do dado do erro do processamento.

**Custo aceito:** cada consulta paga uma conversão de coordenadas, mitigado
pela memorização do transformador.

### Geometria do OpenStreetMap não é versionada
A ODbL exige atribuição e compartilhamento nos mesmos termos para bases
derivadas. A geometria fica em `data/`, reconstruível pelo script de
extração; o repositório publica apenas resultados.

### Passo de amostragem do perfil: 100 m
O perfil é reamostrado a cada 100 m, não a cada 20 m como sugeriria a
estaca convencional.

**Motivo:** amostrar abaixo da resolução do MDE (30 m) produz rampas
artificiais. Medido no traçado real: rampa máxima de 35,26% a 20 m,
25,68% a 30 m, 13,87% a 100 m e 9,30% a 200 m, sem estabilização — padrão
característico de ruído, não de relevo.

**Custo aceito:** feições de relevo com menos de 100 m de extensão não são
representadas. A estaca de 20 m permanece como unidade de apresentação.

**Consequência:** o cálculo de volumes da Sprint 5 herda esta limitação e
deve reportar comparação relativa entre alternativas, não valor absoluto.

### Rede viária carregada completa, classificada depois
A consulta ao OSM traz todas as classes rurais, sem filtro de revestimento.

**Motivo:** o percurso real é misto — pavimentado nas saídas urbanas, leito
natural no meio. Filtrar por surface na consulta desconectava as cidades da
malha rural e produzia "sem caminho contínuo" onde há caminho.

**Custo aceito:** volume maior de dados, contornado por caixa justa (3 km de
margem sobre os dois extremos) em vez de filtro por atributo.

## Pendências

- **Licenciamento de conteúdo não decidido.** A MIT cobre o código. O
  relatório, gráficos e texto do estudo são conteúdo, não software.
  **Gatilho:** se o relatório final for divulgado como peça autônoma,
  avaliar licença dupla (MIT + Creative Commons).

- **Tabela de rampas máximas não verificada na fonte primária.** A referência
  é o Manual de Projeto Geométrico de Rodovias Rurais (DNER/DNIT, 1999). Um
  ponto corroborante de fonte secundária indica 4,5% para Classe I-B em relevo
  ondulado, mas a tabela completa não foi confirmada no manual original.
  **Gatilho:** antes de definir os parâmetros em `config/`, obter o manual e
  conferir os valores por classe e relevo. Nenhum número normativo entra no
  projeto sem essa conferência.

- **README com premissas desatualizadas.** As distâncias de ~25 km em linha
  reta e ~70 km pela via pavimentada vieram da pesquisa inicial e não se
  sustentam. **Gatilho:** encerramento da Sprint 2, quando as distâncias
  estiverem medidas por código. Incluir seção "Revisões de premissa".
- **Licenciamento do OpenStreetMap não avaliado.** A extração da geometria
  viária na Sprint 3 usará dados ODbL, com exigência de atribuição e cláusula
  de compartilhamento para bases derivadas. **Gatilho:** antes de publicar
  qualquer geometria derivada no repositório.
- **Situação real da obra.** A fonte oficial registra recuperação do leito
  natural em curso; o asfaltamento permanece como expectativa, não como obra
  contratada. **Gatilho:** ajustar o texto do README junto com as premissas.

- **Aviso de atribuição do Copernicus ausente no README.** **Gatilho:**
  antes de divulgar o repositório.
- **Ponto de conexão em Esteios provisório.** A sede da vila é referência
  temporária; o nó correto é o entroncamento MG-429/MG-176, confirmado por
  imagem. **Gatilho:** Sprint 3, com a geometria viária do OpenStreetMap.

- **Trechos sem tag surface excluídos.** A consulta de geometria filtra por
  revestimento não pavimentado, deixando de fora os 44 trechos rurais sem a
  tag. Se o traçado em estudo estiver entre eles, não aparecerá.
  **Gatilho:** se a análise de conectividade não encontrar caminho contínuo
  entre Bambuí e o entroncamento.

- **Vales dos km 22 a 28 possivelmente subestimados.** Um MDE de 30 m não
  alcança o fundo de talvegues estreitos: a célula média inclui as encostas.
  Some-se o risco R10, já que vales têm mata ciliar. **Gatilho:** Sprint 5,
  no cálculo de volumes — reportar comparação relativa, não valor absoluto,
  e registrar sensibilidade nesse trecho.

## Descobertas

- `git status` colapsa diretórios sem arquivos rastreados, mostrando apenas
  o nome da pasta. Usar `git status -uall` para listar arquivo a arquivo.
- `git check-ignore -v` com saída iniciada por `!` indica reinclusão
  bem-sucedida, não exclusão. Ausência de saída significa que nenhum padrão
  toca o caminho.
- Steps do GitHub Actions rodam em shells independentes; ambientes conda não
  persistem entre eles. O bloco `defaults: run: shell: bash -el {0}` é o que
  garante a ativação em cada step.

- Um `__post_init__` com o nome digitado errado não gera erro algum: vira um
  método comum que nunca é chamado, desligando silenciosamente toda a
  validação da dataclass. Só um teste de validação detecta.
- Em um `TypeError`, o tipo citado na mensagem identifica a causa: 'method'
  indica parênteses ausentes na chamada; 'tuple' indica coleção passada onde
  se esperava um elemento.

- Esteios é vila do município de Luz, não distrito de Bambuí. Confirmado no
  Cadastro de Localidades Selecionadas do IBGE.
- A distância em linha reta é limite inferior absoluto para qualquer traçado
  rodoviário. Verificação de sanidade que reprovou a extensão de 22 km
  atribuída ao trecho Bambuí–Esteios, cuja linha reta é da ordem de 30 km.
- Sínteses automatizadas de pesquisa podem apresentar citações plausíveis que
  não correspondem ao conteúdo da fonte. Toda referência deste projeto é
  verificada no documento original antes de ser adotada.

- Cada tile do Copernicus vem acompanhado de máscaras auxiliares: corpos
  d'água (WBM) e edição (EDM). Podem ser úteis no tratamento de vales na
  Sprint 5.
- Requisição HEAD informa a existência e o tamanho de um recurso sem
  transferi-lo. Comparar esse tamanho com o do arquivo em disco é a
  verificação mais barata contra download parcial.
- Teste de URL montada deve verificar a estrutura completa do caminho, não
  apenas prefixo e sufixo: um teste que checava só as pontas passou sobre
  uma URL a que faltava um segmento inteiro.

- O Copernicus GLO-30 não declara nodata nos metadados. Células sem dado
  válido aparecem como cota exatamente zero. No recorte do corredor, 6,3%
  das células são zero, todas explicadas por 86 colunas e uma linha nas
  bordas e na emenda entre os tiles. Nenhuma no corredor de estudo. A menor
  cota legítima observada é 622,3 m.
- Os tiles do bucket estão em EPSG:4326 (WGS 84), não em EPSG:4674
  (SIRGAS 2000). A diferença é submétrica no Brasil, irrelevante diante de
  células de 30 m, mas a implementação da porta deve ler o CRS do arquivo
  em vez de presumi-lo.

- Aferição do MDE contra as altitudes do IBGE nas três localidades:
  diferenças de -3,3 m (Bambuí), -5,0 m (Esteios) e +2,4 m (Luz). Maior
  diferença absoluta 5,0 m, viés médio -2,0 m. Sinais alternados indicam
  ruído aleatório, não deslocamento sistemático de referência vertical.
  A cadeia de coordenadas, projeção e amostragem está validada por fonte
  independente.

  - No OSM, o revestimento é bem mapeado no corredor Bambuí–Esteios: dos 569
  trechos rurais, 407 são não pavimentados (unpaved ou ground) e apenas 44
  não têm a tag surface. Porém nenhum trecho designado MG-429 aparece sem
  pavimentação, o que sugere que o leito natural está mapeado sem a
  designação estadual. A identificação do traçado em estudo deve ser feita
  por geometria, não por designação.

  - A API Overpass falha com 500, 502 ou 504 quando a consulta é volumosa
  demais, sem indicar o motivo. Uma consulta mínima na mesma instância
  distingue serviço indisponível de consulta pesada: 428 trechos numa caixa
  de 2 km de lado revelaram que a malha urbana dominava o pedido original.
  Filtrar por revestimento na origem reduziu o resultado a 407 trechos e
  7.639 vértices.
- A instância overpass.kumi.systems falhou mesmo com consulta trivial;
  descartada como alternativa.

- Caminho mínimo Bambuí-Esteios na rede do OSM: 37,31 km, sendo 27,97 km
  de leito natural (75%) e 9,35 km de asfalto nas saídas urbanas (25%).
  Sinuosidade de 1,23 sobre os 30,22 km de linha reta. Substitui, por
  medição própria, a extensão de 22 km atribuída ao trecho de terra na
  pesquisa inicial.
- Filtrar por atributo na consulta quebra a análise de conectividade: o
  percurso real é misto, e filtrar por revestimento não pavimentado
  desconectava as cidades da malha rural. Carregar a rede completa e
  classificar depois.
- Grafo de malha viária deve ser montado vértice a vértice, não pelos
  extremos dos trechos: 181 dos 557 extremos eram pontos interiores de
  outros trechos, e o modelo por extremos produzia 170 componentes onde
  havia 31.

- Perfil do traçado existente Bambuí-Esteios (passo 100 m): amplitude de
  122,7 m entre 639 e 762 m. Sobe 80 m ao sair de Bambuí até o divisor no
  km 5, mantém platô ondulado entre os km 6 e 22, e atravessa dois vales
  profundos entre os km 22 e 28, ambos descendo a cerca de 640 m. O trecho
  crítico do estudo é esse intervalo de 6 km.
- Erro de ponto médio não é detectado por teste na camada de apresentação:
  a figura saiu com eixo horizontal ao dobro da escala por uma divisão
  ausente. Inspeção visual é a verificação dessa camada.
