"""Entidades e regras de engenharia rodoviária.

Camada central do sistema. Contém traçados, perfis longitudinais, greides,
classes de rodovia e cálculos de declividade, rampa máxima e volumes de
terraplenagem.

Esta camada é Python puro: não lê arquivos, não acessa a rede e não importa
bibliotecas geoespaciais. Opera exclusivamente sobre coordenadas métricas
projetadas, nunca sobre graus decimais.
"""