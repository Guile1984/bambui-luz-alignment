"""Leitura de elevação a partir de um modelo digital em formato raster.

Implementa o contrato ProvedorElevacao sobre um arquivo georreferenciado.
O sistema de referência do arquivo é lido dos seus metadados, não
presumido: a fonte pode publicar em datum distinto do adotado no estudo.
"""

from collections.abc import Sequence
from pathlib import Path
from types import TracebackType

import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window

from bambui_luz.config.estudo import CRS_TRABALHO
from bambui_luz.domain.geometria import Ponto
from bambui_luz.infrastructure.coordenadas import criar_transformador
from bambui_luz.ports.elevacao import ElevacaoIndisponivelError

COTA_AUSENTE = 0.0
"""Valor que a fonte utilia para células sem dado, sem declará-lo nos metadados.

O Copernicus GLO-30 não informa nodata no arquivo. Células sem dados válido
aparecem como zero exato, valor que nenhum cota legítima da região assume.
"""


class ProvedorElevacaoRaster:
    """Fornece elevação amostrando um raster georreferenciado.

    Mantém o arquivo aberto durante seu tempo de vida. Use como gerenciador
    de contexto para garantir o fechamento.

    Attributes:
        caminho: Arquivo raster de origem.
    """

    def __init__(self, caminho: Path) -> None:
        """Abre o raster e prepara a conversão de coordenadas.

        Args:
            caminho: Arquivo raster georreferenciado.

        Raises:
            FileNotFoundError: Se o arquivo não existir.
        """
        if not caminho.exists():
            raise FileNotFoundError(f"modelo de elevação não encontrado: {caminho}")
        self.caminho = caminho
        self._raster = rasterio.open(caminho)
        self._transformador = criar_transformador(
            CRS_TRABALHO, self._raster.crs.to_string()
        )

    def __enter__(self) -> "ProvedorElevacaoRaster":
        """Retorna o próprio provedor ao entrar no contexto."""
        return self

    def __exit__(
        self,
        tipo: type[BaseException] | None,
        valor: BaseException | None,
        traco: TracebackType | None,
    ) -> None:
        """Fecha o raster ao sair do contexto."""
        self.fechar()

    def fechar(self) -> None:
        """Libera o arquivo raster."""
        self._raster.close()

    def cotas_em(self, pontos: Sequence[Ponto]) -> tuple[float, ...]:
        """Obtém a elevação de cada ponto informado.

        Args:
            pontos: Pontos em coordenadas métricas projetadas.

        Returns:
            Cotas em metros, na mesma ordem dos pontos recebidos.

        Raises:
            ElevacaoIndisponivelError: Se algum ponto estiver fora da
                cobertura do raster ou sobre célula sem dado válido.
        """
        return tuple(self._cota_de(ponto) for ponto in pontos)

    def _cota_de(self, ponto: Ponto) -> float:
        """Amostra a elevação de um ponto com interpolação bilinear.

        Args:
            ponto: Ponto em coordenadas métricas projetadas.

        Returns:
            Cota em metros.

        Raises:
            ElevacaoIndisponivelError: Se o ponto estiver fora da cobertura
                ou sobre célula sem dado válido.
        """
        x_fonte, y_fonte = self._transformador.transform(ponto.x, ponto.y)
        linha, coluna = self._raster.index(x_fonte, y_fonte)

        if not (0 <= linha < self._raster.height and 0 <= coluna < self._raster.width):
            raise ElevacaoIndisponivelError(
                f"ponto fora da cobertura do modelo de elevação: "
                f"({ponto.x:.1f}, {ponto.y:.1f}) em {CRS_TRABALHO}"
            )
        janela = Window(col_off=coluna, row_off=linha, width=1, height=1)
        amostra = self._raster.read(
            1, window=janela, resampling=Resampling.bilinear, boundless=True
        )
        cota = float(amostra[0, 0])

        nodata = self._raster.nodata
        if cota == COTA_AUSENTE or (nodata is not None and cota == nodata):
            raise ElevacaoIndisponivelError(
                f"célula sem dado válido de elevação em "
                f"({ponto.x:.1f}, {ponto.y:.1f}): cota lida {cota}"
            )
        return cota
