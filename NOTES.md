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

## Pendências

- **Licenciamento de conteúdo não decidido.** A MIT cobre o código. O
  relatório, gráficos e texto do estudo são conteúdo, não software.
  **Gatilho:** se o relatório final for divulgado como peça autônoma,
  avaliar licença dupla (MIT + Creative Commons).

## Descobertas

- `git status` colapsa diretórios sem arquivos rastreados, mostrando apenas
  o nome da pasta. Usar `git status -uall` para listar arquivo a arquivo.
- `git check-ignore -v` com saída iniciada por `!` indica reinclusão
  bem-sucedida, não exclusão. Ausência de saída significa que nenhum padrão
  toca o caminho.
- Steps do GitHub Actions rodam em shells independentes; ambientes conda não
  persistem entre eles. O bloco `defaults: run: shell: bash -el {0}` é o que
  garante a ativação em cada step.
