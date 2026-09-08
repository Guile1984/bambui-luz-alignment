"""Executa a sequência completa do estudo, do download à figura final.

Verifica na prática a reprodutibilidade que o README afirma. As etapas são
idempotentes: arquivos já presentes não são rebaixados, e processamentos
são refeitos sobre os dados existentes.

Dados do OpenStreetMap (ODbL) e de elevação Copernicus DEM.
"""

import subprocess
import sys
import time
from pathlib import Path

NOTEBOOKS = Path("notebooks")

ETAPAS = [
    ("Download dos tiles de elevação", "baixar_mde.py"),
    ("Recorte do corredor de estudo", "gerar_recorte.py"),
    ("Download da rede viária", "baixar_rede_completa.py"),
    ("Geração da alternativa por menor custo", "gerar_alternativa.py"),
    ("Análise de sensibilidade aos pesos", "sensibilidade_dois_pesos.py"),
    ("Comparação geométrica das alternativas", "comparar_tracados.py"),
    ("Cálculo de terraplenagem", "calcular_terraplenagem.py"),
    ("Relatório consolidado", "gerar_relatorio.py"),
    ("Perfil longitudinal do traçado existente", "extrair_perfil_real.py"),
    ("Figura do perfil", "desenhar_perfil_real.py"),
    ("Figuras do diagrama de massa", "desenhar_massa.py"),
    ("Mapa comparativo", "desenhar_mapa_comparativo.py"),
]


def executar(descricao: str, script: str) -> float:
    """Executa um script do estudo e reporta o resultado.

    Args:
        descricao: Texto descritivo da etapa.
        script: Nome do arquivo em notebooks/.

    Returns:
        Duração da execução, em segundos.

    Raises:
        SystemExit: Se o script falhar.
    """
    caminho = NOTEBOOKS / script
    if not caminho.exists():
        print(f"  FALHA — script não encontrado: {caminho}")
        raise SystemExit(1)

    inicio = time.perf_counter()
    resultado = subprocess.run(
        [sys.executable, str(caminho)],
        capture_output=True,
        text=True,
        check=False,
    )
    duracao = time.perf_counter() - inicio

    if resultado.returncode != 0:
        print(f"  FALHA após {duracao:.1f} s (código {resultado.returncode})")
        print("\n--- saída padrão ---")
        print(resultado.stdout[-2000:])
        print("\n--- saída de erro ---")
        print(resultado.stderr[-2000:])
        raise SystemExit(resultado.returncode)

    return duracao


print("Reprodução completa do estudo bambui-luz-alignment\n")
duracoes = []
for indice, (descricao, script) in enumerate(ETAPAS, start=1):
    print(f"[{indice:>2}/{len(ETAPAS)}] {descricao}...")
    duracao = executar(descricao, script)
    duracoes.append((descricao, duracao))
    print(f"  concluída em {duracao:.1f} s")

total = sum(duracao for _, duracao in duracoes)
print(f"\nTodas as {len(ETAPAS)} etapas concluídas em {total:.1f} s\n")
print(f"{'Etapa':<45}{'Duração (s)':>12}")
print("-" * 57)
for descricao, duracao in duracoes:
    print(f"{descricao:<45}{duracao:>12.1f}")

print("\nArtefatos gerados em data/processed:")
for arquivo in sorted(Path("data/processed").glob("*")):
    print(f"  {arquivo.name:<40}{arquivo.stat().st_size / 1024**2:>8.2f} MB")
