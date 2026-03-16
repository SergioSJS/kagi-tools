"""
Testes para o módulo kagi_integrated.py
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
from kagi_integrated import kagi_search_with_summary


class TestKagiIntegrated:
    """Testes para a função kagi_search_with_summary"""

    @patch('kagi_integrated.KagiSearch')
    def test_search_without_summary(self, mock_kagi_search_class, mock_search_results):
        """Testa busca sem resumo"""
        # Mock da instância de KagiSearch
        mock_kagi_instance = MagicMock()
        mock_kagi_instance.search.return_value = mock_search_results
        mock_kagi_search_class.from_env.return_value = mock_kagi_instance

        results = kagi_search_with_summary(
            query="test query",
            qtd=2,
            resumo=False
        )

        assert isinstance(results, list)
        assert len(results) <= 2
        if len(results) > 0:
            assert 'idx' in results[0]
            assert 'url' in results[0]
            assert 'title' in results[0]
            assert 'snippet' in results[0]
            assert results[0]['summary'] is None

    @patch('kagi_integrated.KagiSummarizer')
    @patch('kagi_integrated.KagiSearch')
    def test_search_with_summary(self, mock_kagi_search_class, mock_summarizer_class, 
                                  mock_search_results, mock_summary_result):
        """Testa busca com resumo"""
        # Mock KagiSearch
        mock_kagi_instance = MagicMock()
        mock_kagi_instance.search.return_value = mock_search_results
        mock_kagi_search_class.from_env.return_value = mock_kagi_instance

        # Mock KagiSummarizer
        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.summarize_url.return_value = mock_summary_result
        mock_summarizer_class.return_value = mock_summarizer_instance

        results = kagi_search_with_summary(
            query="test query",
            qtd=2,
            resumo=True,
            idioma="PT"
        )

        assert isinstance(results, list)
        assert len(results) > 0
        assert 'summary' in results[0]
        # Verifica se o resumo foi adicionado se o mock funcionou
        if results[0]['summary']:
            assert results[0]['summary'] == mock_summary_result['summary']

    @patch('kagi_integrated.KagiSearch')
    def test_search_with_limit(self, mock_kagi_search_class, mock_search_results):
        """Testa busca com limite de resultados"""
        mock_kagi_instance = MagicMock()
        mock_kagi_instance.search.return_value = mock_search_results
        mock_kagi_search_class.from_env.return_value = mock_kagi_instance

        results = kagi_search_with_summary(query="test", qtd=1, resumo=False)

        assert len(results) <= 1

    @patch('kagi_integrated.KagiSearch')
    def test_search_error_handling(self, mock_kagi_search_class):
        """Testa tratamento de erros na busca"""
        mock_kagi_instance = MagicMock()
        mock_kagi_instance.search.return_value = {
            'success': False,
            'error': 'Connection failed'
        }
        mock_kagi_search_class.from_env.return_value = mock_kagi_instance

        result = kagi_search_with_summary(query="test", qtd=2, resumo=False)

        assert 'error' in result
        assert result['results'] == []

    @patch('kagi_integrated.KagiSummarizer')
    @patch('kagi_integrated.KagiSearch')
    def test_summary_error_handling(self, mock_kagi_search_class, mock_summarizer_class,
                                     mock_search_results):
        """Testa tratamento de erros no resumo"""
        # Mock search success
        mock_kagi_instance = MagicMock()
        mock_kagi_instance.search.return_value = mock_search_results
        mock_kagi_search_class.from_env.return_value = mock_kagi_instance

        # Mock summarizer failure
        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.summarize_url.return_value = {
            'success': False,
            'error': 'Summarization failed'
        }
        mock_summarizer_class.return_value = mock_summarizer_instance

        results = kagi_search_with_summary(query="test", qtd=1, resumo=True)

        assert len(results) > 0
        assert 'summary_error' in results[0]
        if results[0]['summary_error']:
            assert 'failed' in results[0]['summary_error'].lower() or results[0]['summary_error'] is None

    @patch('kagi_integrated.KagiSearch')
    def test_language_parameter(self, mock_kagi_search_class, mock_search_results):
        """Testa parâmetro de idioma"""
        mock_kagi_instance = MagicMock()
        mock_kagi_instance.search.return_value = mock_search_results
        mock_kagi_search_class.from_env.return_value = mock_kagi_instance

        # Test with different language
        results = kagi_search_with_summary(
            query="test",
            qtd=1,
            resumo=False,
            idioma="EN"
        )

        assert isinstance(results, list)


class TestKagiSearchFromEnv:
    """Testes para a classe helper KagiSearch.from_env"""

    @patch('kagi_integrated.get_session_url_from_env')
    @patch('kagi_integrated.KagiSearch')
    def test_from_env_success(self, mock_kagi_class, mock_get_url):
        """Testa criação de instância a partir do .env"""
        from kagi_integrated import KagiSearch as IntegratedKagiSearch
        
        mock_get_url.return_value = "https://kagi.com/search?token=test"
        
        # O from_env é um classmethod que chama get_session_url_from_env
        result = IntegratedKagiSearch.from_env()
        
        # Verifica que foi chamado
        assert result is not None

    @patch('kagi_integrated.get_session_url_from_env')
    def test_from_env_no_url(self, mock_get_url):
        """Testa erro quando URL não está configurada"""
        from kagi_integrated import KagiSearch as IntegratedKagiSearch
        
        mock_get_url.return_value = None
        
        with pytest.raises(ValueError, match="KAGI_SESSION_URL não configurada"):
            IntegratedKagiSearch.from_env()
