"""Implementações concretas de acesso a dados geoespaciais.

Única camada que conhece rasterio, pyproj, shapely e geopandas. Responde
pelo download e recorte do modelo digital de elevação, pela reprojeção de
coordenadas e pela leitura e escrita de arquivos vetoriais.

Concentra aqui a fragilidade do projeto: dependências binárias, formatos de
arquivo e fontes externas de dados.
"""
