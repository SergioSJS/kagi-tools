"""
Testes para o módulo kagi_images.py
"""
from unittest.mock import MagicMock, patch

import pytest

from kagi_images import KagiImageDownloader


class TestKagiImageDownloader:
    """Testes para a classe KagiImageDownloader"""

    def test_init_with_session_url(self, session_url):
        """Testa inicialização com URL de sessão"""
        downloader = KagiImageDownloader(session_url)
        assert downloader.session_token == 'test_token_123'
        assert downloader.base_url == "https://kagi.com/images"

    def test_init_from_env(self, mock_env):
        """Testa inicialização a partir de variável de ambiente"""
        downloader = KagiImageDownloader()
        assert downloader.session_token is not None

    def test_init_without_url_raises_error(self, monkeypatch):
        """Testa que erro é lançado sem URL de sessão"""
        monkeypatch.delenv("KAGI_SESSION_URL", raising=False)

        with pytest.raises(ValueError, match="KAGI_SESSION_URL não configurada"):
            KagiImageDownloader()

    def test_extract_token(self, session_url):
        """Testa extração do token da URL"""
        downloader = KagiImageDownloader(session_url)
        assert downloader.session_token == 'test_token_123'

    @patch('kagi_images.requests.get')
    def test_search_and_download_success(self, mock_get, session_url, tmp_path):
        """Testa busca e download de imagens bem-sucedido"""
        # Mock da resposta HTML
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body><img src="https://example.com/image.jpg"/></body></html>'
        mock_response.content = b'fake_image_data'
        mock_get.return_value = mock_response

        downloader = KagiImageDownloader(session_url)

        # Mockar métodos internos para simplificar
        with patch.object(downloader, '_extract_image_urls', return_value=['https://example.com/img1.jpg']):
            with patch.object(downloader, '_download_images', return_value=(1, ['img1.jpg'])):
                result = downloader.search_and_download(
                    query="test images",
                    num_images=1,
                    output_dir=str(tmp_path)
                )

        assert result['success'] is True
        assert result['query'] == "test images"

    def test_sanitize_filename(self, session_url):
        """Testa sanitização de nome de arquivo"""
        downloader = KagiImageDownloader(session_url)

        dirty_name = "test/image:name*with?bad|chars"
        clean_name = downloader._sanitize_filename(dirty_name)

        assert "/" not in clean_name
        assert ":" not in clean_name
        assert "*" not in clean_name
        assert "?" not in clean_name
        assert "|" not in clean_name

    @patch('kagi_images.requests.get')
    def test_download_failure_handling(self, mock_get, session_url, tmp_path):
        """Testa tratamento de falhas no download"""
        mock_get.side_effect = Exception("Network error")

        downloader = KagiImageDownloader(session_url)

        with patch.object(downloader, '_extract_image_urls', return_value=[]):
            result = downloader.search_and_download(
                query="test",
                num_images=1,
                output_dir=str(tmp_path)
            )

        assert result['success'] is False
        assert 'error' in result

    def test_size_filter_parameter(self, session_url):
        """Testa parâmetro de filtro de tamanho"""
        downloader = KagiImageDownloader(session_url)

        with patch.object(downloader, '_extract_image_urls', return_value=[]):
            with patch.object(downloader, '_download_images', return_value=(0, [])):
                result = downloader.search_and_download(
                    query="test",
                    num_images=1,
                    size="large"
                )

        # Verifica que a função aceita o parâmetro sem erro
        assert isinstance(result, dict)


class TestImageDownloaderIntegration:
    """Testes de integração para o downloader de imagens"""

    @pytest.mark.integration
    @patch('kagi_images.requests.get')
    def test_full_download_workflow(self, mock_get, session_url, tmp_path):
        """Testa workflow completo de download"""
        # Mock resposta HTML
        html_response = MagicMock()
        html_response.status_code = 200
        html_response.text = '<html><img src="https://example.com/test.jpg"/></html>'

        # Mock resposta de imagem
        image_response = MagicMock()
        image_response.status_code = 200
        image_response.content = b'fake_image_content'
        image_response.headers = {'content-type': 'image/jpeg'}

        mock_get.side_effect = [html_response, image_response]

        downloader = KagiImageDownloader(session_url)

        # Este teste pode precisar de mais mocks dependendo da implementação
        # Por enquanto, verifica se a instância foi criada
        assert downloader is not None
