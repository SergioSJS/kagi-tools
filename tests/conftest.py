"""
Configuração compartilhada de testes pytest
"""

import pytest


@pytest.fixture
def mock_env(monkeypatch):
    """Mock de variável de ambiente KAGI_SESSION_URL"""
    session_url = "https://kagi.com/search?token=test_token_123"
    monkeypatch.setenv("KAGI_SESSION_URL", session_url)
    return session_url


@pytest.fixture
def session_url():
    """Retorna URL de sessão para testes"""
    return "https://kagi.com/search?token=test_token_123&q=test"


@pytest.fixture
def mock_html_response():
    """HTML de exemplo com resultados de busca"""
    return """
    <html>
        <body>
            <div class="search-result">
                <a href="https://example.com/result1">Result 1 Title</a>
                <p>This is the description for result 1</p>
            </div>
            <div class="search-result">
                <a href="https://example.com/result2">Result 2 Title</a>
                <p>This is the description for result 2</p>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_search_results():
    """Resultados de busca de exemplo"""
    return {
        "success": True,
        "query": "test query",
        "total": 2,
        "results": [
            {
                "title": "Example Result 1",
                "url": "https://example.com/1",
                "snippet": "This is an example result",
            },
            {
                "title": "Example Result 2",
                "url": "https://example.com/2",
                "snippet": "Another example result",
            },
        ],
    }


@pytest.fixture
def mock_summary_result():
    """Resultado de sumarização de exemplo"""
    return {
        "success": True,
        "url": "https://example.com/article",
        "summary": "This is a summary of the article content.",
        "language": "EN",
        "type": "summary",
    }
