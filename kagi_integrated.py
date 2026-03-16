#!/usr/bin/env python3
"""
Kagi Integrado - Busca com resumo opcional
"""

import json
from kagi_simple import KagiSearch
from kagi_summarizer import KagiSummarizer
import time


def kagi_search_with_summary(
    query: str,
    qtd: int = 2,
    resumo: bool = False,
    idioma: str = "PT",
    session_url: str = None
) -> list:
    """
    Busca no Kagi com resumo opcional dos resultados
    
    Args:
        query: Termo de busca
        qtd: Número de resultados (default: 2)
        resumo: Se deve resumir cada URL (default: False)
        idioma: Idioma do resumo (default: PT)
        session_url: URL de sessão (opcional, pega do .env se não fornecido)
    
    Returns:
        Lista de dicionários com resultados no formato:
        [
            {
                "idx": 1,
                "url": "...",
                "title": "...",
                "snippet": "...",  # Descrição curta do resultado
                "summary": "...",   # Resumo completo (se resumo=True)
                "summary_error": None  # Erro ao resumir (se houver)
            }
        ]
    """
    results = []
    
    # 1. Fazer busca
    try:
        kagi_search = KagiSearch(session_url) if session_url else KagiSearch.from_env()
        search_results = kagi_search.search(query)
        
        if not search_results['success']:
            return {
                'error': search_results.get('error', 'Erro na busca'),
                'results': []
            }
        
        # Limitar resultados
        search_items = search_results['results'][:qtd]
        
    except Exception as e:
        return {
            'error': f'Erro ao buscar: {str(e)}',
            'results': []
        }
    
    # 2. Processar cada resultado
    summarizer = None
    if resumo:
        try:
            summarizer = KagiSummarizer(session_url)
        except Exception as e:
            # Se falhar ao criar summarizer, continua sem resumo
            resumo = False
    
    for idx, item in enumerate(search_items, 1):
        result = {
            'idx': idx,
            'url': item['url'],
            'title': item['title'],
            'snippet': item.get('snippet', ''),
            'summary': None,
            'summary_error': None
        }
        
        # 3. Resumir se solicitado
        if resumo and summarizer:
            try:
                print(f"📝 Resumindo {idx}/{len(search_items)}: {item['title'][:50]}...")
                summary_result = summarizer.summarize_url(
                    item['url'],
                    target_language=idioma,
                    summary_type='summary'
                )
                
                if summary_result['success']:
                    result['summary'] = summary_result['summary']
                else:
                    result['summary_error'] = summary_result.get('error', 'Erro desconhecido')
                    
            except Exception as e:
                result['summary_error'] = str(e)
        
        results.append(result)
    
    return results


# Versão alternativa para compatibilidade
class KagiSearch:
    @classmethod
    def from_env(cls):
        """Cria instância pegando URL do .env"""
        from kagi_simple import get_session_url_from_env
        url = get_session_url_from_env()
        if not url:
            raise ValueError("KAGI_SESSION_URL não configurada no .env")
        from kagi_simple import KagiSearch as KS
        return KS(url)


def main():
    """Exemplo de uso"""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python kagi_integrated.py 'query' [--qtd N] [--resumo] [--lang XX]")
        print("\nExemplos:")
        print("  python kagi_integrated.py 'python tutorial'")
        print("  python kagi_integrated.py 'machine learning' --qtd 3")
        print("  python kagi_integrated.py 'AI news' --qtd 2 --resumo")
        print("  python kagi_integrated.py 'AI news' --qtd 2 --resumo --lang EN")
        sys.exit(1)
    
    query = sys.argv[1]
    
    # Parse argumentos
    qtd = 2
    resumo = '--resumo' in sys.argv
    idioma = 'PT'
    
    if '--qtd' in sys.argv:
        idx = sys.argv.index('--qtd')
        if idx + 1 < len(sys.argv):
            qtd = int(sys.argv[idx + 1])
    
    if '--lang' in sys.argv:
        idx = sys.argv.index('--lang')
        if idx + 1 < len(sys.argv):
            idioma = sys.argv[idx + 1]
    
    print(f"\n🔍 Buscando: {query}")
    print(f"📊 Resultados: {qtd}")
    print(f"📝 Resumo: {'Sim' if resumo else 'Não'}")
    if resumo:
        print(f"🌐 Idioma: {idioma}")
    print()
    
    start_time = time.time()
    
    results = kagi_search_with_summary(
        query=query,
        qtd=qtd,
        resumo=resumo,
        idioma=idioma
    )
    
    elapsed = time.time() - start_time
    
    # Exibir resultados
    print("\n" + "=" * 70)
    print("RESULTADOS")
    print("=" * 70)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print("=" * 70)
    print(f"⏱️  Tempo: {elapsed:.2f}s")
    print()


if __name__ == "__main__":
    main()
