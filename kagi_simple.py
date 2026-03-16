#!/usr/bin/env python3
"""
Kagi Search - Busca simples usando URL com sessão
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse, parse_qs
import json
import sys
import os


class KagiSearch:
    """Cliente simples para buscar no Kagi usando URL com sessão"""
    
    def __init__(self, session_url: str):
        """
        Args:
            session_url: URL do Kagi com sessão (ex: https://kagi.com/search?token=abc123&q=test)
        """
        self.session_url = session_url
        self.base_url = self._extract_base_url(session_url)
        self.session_params = self._extract_session_params(session_url)
        
    def _extract_base_url(self, url: str) -> str:
        """Extrai a URL base"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    def _extract_session_params(self, url: str) -> dict:
        """Extrai parâmetros de sessão da URL (exceto a query)"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        # Converter de lista para valores únicos e remover 'q'
        session_params = {}
        for key, value in params.items():
            if key != 'q':
                session_params[key] = value[0] if isinstance(value, list) else value
        return session_params
    
    def search(self, query: str, debug: bool = False) -> dict:
        """
        Faz uma busca
        
        Args:
            query: Termo de busca
            debug: Se True, salva o HTML para debug
            
        Returns:
            Dict com resultados
        """
        # Usar versão HTML (sem JavaScript) do Kagi
        # A versão normal carrega resultados via JS
        html_base_url = self.base_url.replace('/search', '/html/search')
        
        # Montar parâmetros (sessão + query)
        params = self.session_params.copy()
        params['q'] = query
        
        try:
            response = requests.get(html_base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Debug: salvar HTML
            if debug:
                with open('debug_kagi.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"📄 HTML salvo em debug_kagi.html")
            
            # Parsear resultados
            results = self._parse_html(response.text, debug=debug)
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'total': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'results': []
            }
    
    def _parse_html(self, html: str, debug: bool = False) -> list:
        """Parse do HTML de resultados"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        if debug:
            print(f"\n🔍 Debug: Procurando resultados no HTML...")
            print(f"   Tamanho do HTML: {len(html)} caracteres")
        
        # Kagi usa várias estruturas possíveis, vamos tentar todas
        
        # Tentativa 1: Procurar por divs com class contendo 'result'
        result_divs = soup.find_all('div', class_=lambda x: x and 'search' in str(x).lower() and 'result' in str(x).lower())
        
        # Tentativa 2: Procurar por elementos com data-testid
        if not result_divs:
            result_divs = soup.find_all(['div', 'li'], attrs={'data-testid': lambda x: x and 'result' in str(x).lower()})
        
        # Tentativa 3: Procurar estrutura típica de resultados de busca
        if not result_divs:
            # Procurar divs que contenham um link e uma descrição
            all_divs = soup.find_all('div', class_=True)
            for div in all_divs:
                links = div.find_all('a', href=True, limit=2)
                has_external_link = any(
                    link.get('href', '').startswith('http') and 'kagi.com' not in link.get('href', '')
                    for link in links
                )
                if has_external_link and len(div.get_text(strip=True)) > 50:
                    result_divs.append(div)
        
        # Processar os divs encontrados
        seen_urls = set()
        for div in result_divs:
            # Encontrar o link principal
            main_link = None
            for link in div.find_all('a', href=True):
                href = link.get('href', '')
                # Filtrar: deve ser externo, não ser widget/ferramenta do Kagi
                if (href.startswith('http') and 
                    'kagi.com' not in href and
                    'wolframalpha.com' not in href and
                    'google.com' not in href and
                    'duckduckgo.com' not in href and
                    href not in seen_urls):
                    main_link = link
                    seen_urls.add(href)
                    break
            
            if not main_link:
                continue
            
            title = main_link.get_text(strip=True)
            url = main_link.get('href', '')
            
            # Procurar snippet/descrição no div
            snippet = ''
            # Procurar por elementos que podem conter a descrição
            for elem in div.find_all(['p', 'div', 'span']):
                text = elem.get_text(strip=True)
                # Snippet é geralmente um texto médio/longo que não é o título
                if text and text != title and len(text) > 30 and len(text) < 500:
                    snippet = text
                    break
            
            # Limpar snippet de textos padrão do Kagi
            if snippet:
                # Remover textos comuns do Kagi
                unwanted_texts = [
                    'More results from this site',
                    'Remove results from this site',
                    'Open page in Web Archive',
                    'Raise this site',
                    'Lower this site',
                    'Block this site',
                    'Pin this site'
                ]
                for unwanted in unwanted_texts:
                    snippet = snippet.replace(unwanted, '')
                
                # Limpar caracteres especiais repetidos
                snippet = snippet.strip().strip('â').strip()
                
                # Se ficou muito curto após limpeza, remover
                if len(snippet) < 20:
                    snippet = ''
            
            if title and len(title) > 5:
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet
                })
        
        # Se ainda não encontramos bons resultados, fazer fallback mais agressivo
        if len(results) < 3:
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if (href.startswith('http') and 
                    href not in seen_urls and
                    'kagi.com' not in href and
                    'wolframalpha.com' not in href and
                    'google.com/maps' not in href and
                    'duckduckgo.com' not in href and
                    'wikipedia.org' not in href):  # Wikipedia geralmente é widget
                    
                    title = link.get_text(strip=True)
                    if title and len(title) > 10 and len(title) < 200:
                        results.append({
                            'title': title,
                            'url': href,
                            'snippet': ''
                        })
                        seen_urls.add(href)
                        
                        if len(results) >= 10:
                            break
        
        return results[:15]  # Limitar a 15 resultados


def format_results(data: dict) -> str:
    """Formata resultados para exibição"""
    lines = []
    
    lines.append("=" * 70)
    lines.append(f"🔍 Query: {data['query']}")
    lines.append(f"📊 Resultados: {data['total']}")
    lines.append("=" * 70)
    lines.append("")
    
    if not data['success']:
        lines.append(f"❌ Erro: {data.get('error')}")
        return "\n".join(lines)
    
    if data['total'] == 0:
        lines.append("⚠️  Nenhum resultado encontrado")
        return "\n".join(lines)
    
    for i, result in enumerate(data['results'], 1):
        lines.append(f"{i}. 📌 {result['title']}")
        lines.append(f"   🔗 {result['url']}")
        if result.get('snippet'):
            lines.append(f"   💬 {result['snippet'][:150]}...")
        lines.append("")
    
    return "\n".join(lines)


def get_session_url_from_env() -> str:
    """Obtém a URL de sessão do .env"""
    # Tentar variável de ambiente primeiro
    url = os.environ.get("KAGI_SESSION_URL")
    if url:
        return url
    
    # Tentar ler do .env
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key.strip() == "KAGI_SESSION_URL":
                        return value.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    
    return None


def main():
    # Verificar se tem --debug
    debug = '--debug' in sys.argv
    # Remover --debug dos args
    args = [arg for arg in sys.argv[1:] if arg != '--debug']
    
    # Se passou URL via argumento, usa ela
    if len(args) >= 2:
        session_url = args[0]
        query = " ".join(args[1:])
    # Senão tenta pegar do .env
    elif len(args) >= 1:
        session_url = get_session_url_from_env()
        if not session_url:
            print("❌ KAGI_SESSION_URL não configurada no .env")
            print("\nEdite o arquivo .env e adicione sua URL do Kagi")
            sys.exit(1)
        query = " ".join(args)
    else:
        print("Uso:")
        print("  python kagi_simple.py 'sua busca' [--debug]")
        print("  python kagi_simple.py '<URL_COM_SESSAO>' 'sua busca' [--debug]")
        print("\nConfigure KAGI_SESSION_URL no .env para não precisar passar a URL sempre")
        print("\nOpções:")
        print("  --debug  Salva o HTML da resposta para análise")
        sys.exit(1)
    
    print(f"\n🚀 Iniciando busca no Kagi...")
    print(f"📝 Query: {query}\n")
    
    kagi = KagiSearch(session_url)
    results = kagi.search(query, debug=debug)
    
    print(format_results(results))


if __name__ == "__main__":
    main()
