#!/usr/bin/env python3
"""
Kagi Summarizer - Resumo de textos e URLs
"""

import os
import sys
from urllib.parse import parse_qs, urlencode, urlparse

import requests


class KagiSummarizer:
    """Cliente para usar o Kagi Summarizer"""

    def __init__(self, session_url: str = None):
        """
        Args:
            session_url: URL do Kagi com sessão (mesma da busca)
                        Se não fornecido, tenta ler do .env
        """
        if session_url is None:
            session_url = self._get_session_url_from_env()

        if not session_url:
            raise ValueError("KAGI_SESSION_URL não configurada")

        self.session_token = self._extract_token(session_url)
        self.base_url = "https://kagi.com/summarizer"

    def _get_session_url_from_env(self) -> str:
        """Obtém a URL de sessão do .env"""
        url = os.environ.get("KAGI_SESSION_URL")
        if url:
            return url

        try:
            with open(".env") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == "KAGI_SESSION_URL":
                            return value.strip().strip('"').strip("'")
        except FileNotFoundError:
            pass

        return None

    def _extract_token(self, url: str) -> str:
        """Extrai o token da URL de sessão"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        if "token" in params:
            return params["token"][0]

        return None

    def summarize_url(
        self,
        url: str,
        target_language: str = "PT",
        summary_type: str = "summary",
        engine: str = None,
        debug: bool = False,
    ) -> dict:
        """
        Resume o conteúdo de uma URL

        Args:
            url: URL para resumir
            target_language: Idioma do resumo (PT, EN, etc)
            summary_type: Tipo de resumo (summary, takeaway)
            engine: Engine a usar (cecil, agnes, daphne, muriel)
            debug: Se True, salva HTML para debug

        Returns:
            Dict com o resumo
        """
        params = {"url": url, "target_language": target_language, "summary": summary_type}

        if self.session_token:
            params["token"] = self.session_token

        if engine:
            params["engine"] = engine

        try:
            requests.get(self.base_url, params=params, timeout=60)
            # Construir URL completa
            full_url = f"{self.base_url}?{urlencode(params)}"

            if debug:
                print(f"📍 URL: {full_url[:100]}...")

            # Usar Selenium para renderizar JavaScript
            summary_text = self._fetch_with_selenium(full_url, debug=debug)

            return {
                "success": True,
                "url": url,
                "summary": summary_text,
                "language": target_language,
                "type": summary_type,
            }

        except Exception as e:
            return {"success": False, "url": url, "error": str(e), "summary": None}

    def _fetch_with_selenium(self, url: str, debug: bool = False) -> str:
        """Usa Selenium para pegar o resumo carregado via JS"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait
        except ImportError:
            return "❌ Selenium não instalado. Instale com: pip install selenium"

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(url)

            if debug:
                print("   ⏳ Aguardando resumo carregar...")

            # Esperar o elemento description aparecer e ter conteúdo
            wait = WebDriverWait(driver, 30)
            description = wait.until(EC.presence_of_element_located((By.ID, "description")))

            # Aguardar conteúdo aparecer
            wait.until(lambda d: len(description.text.strip()) > 50)

            summary_text = description.text.strip()

            if debug:
                with open("debug_summary.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("   📄 HTML salvo em debug_summary.html")
                print(f"   ✅ Resumo extraído: {len(summary_text)} caracteres")

            return self._clean_summary_text(summary_text)

        except Exception as e:
            if debug:
                print(f"   ❌ Erro no Selenium: {e}")
            return f"Erro ao carregar resumo: {str(e)}"
        finally:
            if driver:
                driver.quit()

    def _parse_summary_html_old(self, html: str, debug: bool = False) -> str:
        """Método antigo - não funciona pois JS carrega conteúdo"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        if debug:
            print("\n🔍 Debug: Procurando resumo no HTML...")
            print(f"   Tamanho do HTML: {len(html)} caracteres")

        # Método 1: Procurar por classe output
        output_div = soup.find("div", class_=lambda x: x and "output" in str(x).lower())
        if output_div:
            text = output_div.get_text(strip=True)
            if len(text) > 50:
                if debug:
                    print(f"   ✅ Encontrado via class output: {len(text)} caracteres")
                return self._clean_summary_text(text)

        # Método 2: Procurar por ID
        output_div = soup.find(
            "div", id=lambda x: x and ("output" in str(x).lower() or "summary" in str(x).lower())
        )
        if output_div:
            text = output_div.get_text(strip=True)
            if len(text) > 50:
                if debug:
                    print(f"   ✅ Encontrado via ID: {len(text)} caracteres")
                return self._clean_summary_text(text)

        # Método 3: Procurar por pre ou code
        for tag in soup.find_all(["pre", "code"]):
            text = tag.get_text(strip=True)
            if len(text) > 100:
                if debug:
                    print(f"   ✅ Encontrado em {tag.name}: {len(text)} caracteres")
                return self._clean_summary_text(text)

        # Método 4: Procurar por article ou main
        for tag_name in ["article", "main"]:
            tag = soup.find(tag_name)
            if tag:
                text = tag.get_text(strip=True)
                if 100 < len(text) < 10000:
                    if debug:
                        print(f"   ✅ Encontrado em {tag_name}: {len(text)} caracteres")
                    return self._clean_summary_text(text)

        # Método 5: Procurar divs com texto médio
        all_divs = soup.find_all("div")
        text_lengths = []
        for div in all_divs:
            text = div.get_text(strip=True)
            if 100 < len(text) < 10000:
                text_lengths.append((len(text), text, div))

        if text_lengths:
            text_lengths.sort()
            if len(text_lengths) > 2:
                _, text, div = text_lengths[len(text_lengths) // 2]
            else:
                _, text, div = text_lengths[0]

            if debug:
                print(f"   ✅ Encontrado em div (médio): {len(text)} caracteres")
                print(f"   Classes: {div.get('class')}")
            return self._clean_summary_text(text)

        if debug:
            print("   ❌ Nenhum resumo encontrado")

        return "Não foi possível extrair o resumo"

    def _clean_summary_text(self, text: str) -> str:
        """Limpa o texto do resumo"""
        unwanted = [
            "ExpandDiscuss FurtherTime saved reading:minOriginal Document",
            "Tokens:(time elapseds)",
            "Expand",
            "Discuss Further",
            "Time saved reading",
            "Original Document",
            "Tokens:",
            "time elapsed",
        ]

        for phrase in unwanted:
            text = text.replace(phrase, "")

        text = text.strip().strip("•").strip("â").strip()

        return text


def format_summary(data: dict) -> str:
    """Formata o resumo para exibição"""
    lines = []

    lines.append("=" * 70)

    if "url" in data:
        lines.append(f"🔗 URL: {data['url']}")

    lines.append(f"🌐 Idioma: {data.get('language', 'N/A')}")
    lines.append(f"📊 Tipo: {data.get('type', 'N/A')}")
    lines.append("=" * 70)
    lines.append("")

    if not data["success"]:
        lines.append(f"❌ Erro: {data.get('error')}")
        return "\n".join(lines)

    if data.get("summary"):
        lines.append("📄 RESUMO:")
        lines.append("")
        lines.append(data["summary"])
    else:
        lines.append("⚠️  Nenhum resumo gerado")

    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python kagi_summarizer.py <URL> [--debug]")
        print("  python kagi_summarizer.py <URL> --lang EN")
        print("  python kagi_summarizer.py <URL> --type takeaway")
        print("  python kagi_summarizer.py <URL> --engine cecil")
        print("\nOpções:")
        print("  --lang LANG    Idioma do resumo (PT, EN, ES, etc)")
        print("  --type TYPE    Tipo: summary ou takeaway")
        print("  --engine ENG   Engine: cecil, agnes, daphne, muriel")
        print("  --debug        Salva HTML para debug")
        sys.exit(1)

    url = sys.argv[1]

    # Parse opções
    lang = "PT"
    summary_type = "summary"
    engine = None
    debug = "--debug" in sys.argv

    if "--lang" in sys.argv:
        idx = sys.argv.index("--lang")
        if idx + 1 < len(sys.argv):
            lang = sys.argv[idx + 1]

    if "--type" in sys.argv:
        idx = sys.argv.index("--type")
        if idx + 1 < len(sys.argv):
            summary_type = sys.argv[idx + 1]

    if "--engine" in sys.argv:
        idx = sys.argv.index("--engine")
        if idx + 1 < len(sys.argv):
            engine = sys.argv[idx + 1]

    print("\n🔍 Resumindo URL com Kagi...")
    print(f"🌐 URL: {url}")
    print(f"📝 Idioma: {lang}")
    print(f"📊 Tipo: {summary_type}\n")

    try:
        summarizer = KagiSummarizer()
        result = summarizer.summarize_url(url, lang, summary_type, engine, debug)
        print(format_summary(result))
    except ValueError as e:
        print(f"❌ Erro: {e}")
        print("\nConfigure KAGI_SESSION_URL no .env")
        sys.exit(1)


if __name__ == "__main__":
    main()
