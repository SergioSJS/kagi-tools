"""
Testes para o módulo kagi_summarizer.py
"""
from unittest.mock import MagicMock, patch

import pytest

from kagi_summarizer import KagiSummarizer


class TestKagiSummarizer:
    """Testes para a classe KagiSummarizer"""

    def test_init_with_session_url(self, session_url):
        """Testa inicialização com URL de sessão"""
        summarizer = KagiSummarizer(session_url)
        assert summarizer.session_token == 'test_token_123'
        assert summarizer.base_url == "https://kagi.com/summarizer"

    def test_init_from_env(self, mock_env):
        """Testa inicialização a partir de variável de ambiente"""
        summarizer = KagiSummarizer()
        assert summarizer.session_token is not None

    def test_init_without_url_raises_error(self, monkeypatch):
        """Testa que erro é lançado sem URL de sessão"""
        monkeypatch.delenv("KAGI_SESSION_URL", raising=False)

        with pytest.raises(ValueError, match="KAGI_SESSION_URL não configurada"):
            KagiSummarizer()

    def test_extract_token(self, session_url):
        """Testa extração do token da URL"""
        summarizer = KagiSummarizer(session_url)
        assert summarizer.session_token == 'test_token_123'

    def test_extract_token_no_token(self):
        """Testa extração de token quando não existe"""
        url_without_token = "https://kagi.com/search?q=test"
        summarizer = KagiSummarizer(url_without_token)
        assert summarizer.session_token is None

    @patch('kagi_summarizer.webdriver')
    def test_summarize_url_success(self, mock_webdriver, session_url):
        """Testa resumo de URL bem-sucedido"""
        # Mock do Selenium
        mock_driver = MagicMock()
        mock_element = MagicMock()
        mock_element.text = "This is a test summary of the article content."

        mock_driver.find_element.return_value = mock_element
        mock_webdriver.Chrome.return_value.__enter__.return_value = mock_driver

        summarizer = KagiSummarizer(session_url)

        with patch.object(summarizer, '_fetch_with_selenium', return_value="Test summary"):
            result = summarizer.summarize_url("https://example.com/article")

        assert result['success'] is True
        assert 'summary' in result
        assert result['url'] == "https://example.com/article"

    def test_summarize_url_failure(self, session_url):
        """Testa comportamento em caso de falha"""
        summarizer = KagiSummarizer(session_url)

        with patch.object(summarizer, '_fetch_with_selenium', side_effect=Exception("Network error")):
            result = summarizer.summarize_url("https://example.com/article")

        assert result['success'] is False
        assert 'error' in result
        assert result['summary'] is None

    def test_clean_summary_text(self, session_url):
        """Testa limpeza do texto do resumo"""
        summarizer = KagiSummarizer(session_url)

        dirty_text = "ExpandDiscuss Further\nThis is the actual summary\nTime saved reading"
        clean_text = summarizer._clean_summary_text(dirty_text)

        assert "Expand" not in clean_text
        assert "Discuss Further" not in clean_text
        assert "This is the actual summary" in clean_text


class TestSummarizerIntegration:
    """Testes de integração para o Summarizer"""

    @pytest.mark.integration
    @patch('kagi_summarizer.webdriver')
    def test_summarize_with_all_parameters(self, mock_webdriver, session_url):
        """Testa resumo com todos os parâmetros"""
        mock_driver = MagicMock()
        mock_element = MagicMock()
        mock_element.text = "Summary in Portuguese"

        mock_driver.find_element.return_value = mock_element
        mock_webdriver.Chrome.return_value.__enter__.return_value = mock_driver

        summarizer = KagiSummarizer(session_url)

        with patch.object(summarizer, '_fetch_with_selenium', return_value="Summary in Portuguese"):
            result = summarizer.summarize_url(
                url="https://example.com/article",
                target_language="PT",
                summary_type="takeaway",
                engine="muriel"
            )

        assert result['success'] is True
        assert result['language'] == "PT"
        assert result['type'] == "takeaway"
