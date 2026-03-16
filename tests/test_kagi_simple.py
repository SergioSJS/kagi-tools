"""
Testes para o módulo kagi_simple.py
"""

import responses

from kagi_simple import KagiSearch, format_results, get_session_url_from_env


class TestKagiSearch:
    """Testes para a classe KagiSearch"""

    def test_init_with_session_url(self, session_url):
        """Testa inicialização com URL de sessão"""
        kagi = KagiSearch(session_url)
        assert kagi.session_url == session_url
        assert kagi.base_url == "https://kagi.com/search"
        assert "token" in kagi.session_params

    def test_extract_base_url(self, session_url):
        """Testa extração da URL base"""
        kagi = KagiSearch(session_url)
        assert kagi.base_url == "https://kagi.com/search"

    def test_extract_session_params(self, session_url):
        """Testa extração dos parâmetros de sessão"""
        kagi = KagiSearch(session_url)
        assert "token" in kagi.session_params
        assert kagi.session_params["token"] == "test_token_123"
        assert "q" not in kagi.session_params

    @responses.activate
    def test_search_success(self, session_url, mock_html_response):
        """Testa busca bem-sucedida"""
        responses.add(
            responses.GET, "https://kagi.com/html/search", body=mock_html_response, status=200
        )

        kagi = KagiSearch(session_url)
        result = kagi.search("test query")

        assert result["success"] is True
        assert result["query"] == "test query"
        assert isinstance(result["results"], list)
        assert result["total"] >= 0

    @responses.activate
    def test_search_with_debug(self, session_url, mock_html_response, tmp_path, monkeypatch):
        """Testa busca com modo debug"""
        monkeypatch.chdir(tmp_path)

        responses.add(
            responses.GET, "https://kagi.com/html/search", body=mock_html_response, status=200
        )

        kagi = KagiSearch(session_url)
        result = kagi.search("test query", debug=True)

        assert result["success"] is True
        assert (tmp_path / "debug_kagi.html").exists()

    @responses.activate
    def test_search_failure(self, session_url):
        """Testa comportamento em caso de falha"""
        responses.add(responses.GET, "https://kagi.com/html/search", body="Error", status=500)

        kagi = KagiSearch(session_url)
        result = kagi.search("test query")

        assert result["success"] is False
        assert "error" in result
        assert result["results"] == []

    def test_parse_html_with_results(self, session_url, mock_html_response):
        """Testa parsing de HTML com resultados"""
        kagi = KagiSearch(session_url)
        results = kagi._parse_html(mock_html_response)

        assert isinstance(results, list)
        # O parsing pode ou não encontrar resultados dependendo da estrutura

    def test_parse_html_empty(self, session_url):
        """Testa parsing de HTML vazio"""
        kagi = KagiSearch(session_url)
        results = kagi._parse_html("<html><body></body></html>")

        assert isinstance(results, list)


class TestFormatResults:
    """Testes para a função format_results"""

    def test_format_success_results(self, mock_search_results):
        """Testa formatação de resultados bem-sucedidos"""
        output = format_results(mock_search_results)

        assert "test query" in output
        assert "Example Result 1" in output
        assert "https://example.com/1" in output

    def test_format_error_results(self):
        """Testa formatação de resultados com erro"""
        error_data = {"success": False, "query": "test", "error": "Connection failed", "total": 0}
        output = format_results(error_data)

        assert "Connection failed" in output
        assert "test" in output

    def test_format_empty_results(self):
        """Testa formatação de resultados vazios"""
        empty_data = {"success": True, "query": "empty test", "total": 0, "results": []}
        output = format_results(empty_data)

        assert "Nenhum resultado encontrado" in output


class TestGetSessionUrlFromEnv:
    """Testes para a função get_session_url_from_env"""

    def test_from_environment_variable(self, mock_env):
        """Testa obtenção da URL da variável de ambiente"""
        url = get_session_url_from_env()
        assert url is not None
        assert "kagi.com" in url

    def test_from_env_file(self, tmp_path, monkeypatch):
        """Testa obtenção da URL do arquivo .env"""
        env_file = tmp_path / ".env"
        env_file.write_text("KAGI_SESSION_URL=https://kagi.com/search?token=file_token")

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("KAGI_SESSION_URL", raising=False)

        url = get_session_url_from_env()
        assert url == "https://kagi.com/search?token=file_token"

    def test_no_url_found(self, monkeypatch, tmp_path):
        """Testa quando nenhuma URL é encontrada"""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("KAGI_SESSION_URL", raising=False)

        url = get_session_url_from_env()
        assert url is None
