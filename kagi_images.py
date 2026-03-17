#!/usr/bin/env python3
"""
Kagi Image Downloader - Baixa imagens dos resultados de busca do Kagi
"""

import os
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests


class KagiImageDownloader:
    """Cliente para buscar e baixar imagens do Kagi"""

    @classmethod
    def from_env(cls):
        """Cria instância pegando URL do .env"""
        url = os.environ.get("KAGI_SESSION_URL")
        if not url:
            try:
                with open(".env") as f:
                    for line in f:
                        if "=" in (line := line.strip()) and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            if key.strip() == "KAGI_SESSION_URL":
                                url = value.strip().strip('"').strip("'")
                                break
            except FileNotFoundError:
                pass
        if not url:
            raise ValueError("KAGI_SESSION_URL não configurada no .env")
        return cls(url)

    def __init__(self, session_url: str = None):
        """
        Args:
            session_url: URL do Kagi com sessão
                        Se não fornecido, tenta ler do .env
        """
        if session_url is None:
            session_url = self._get_session_url_from_env()

        if not session_url:
            raise ValueError("KAGI_SESSION_URL não configurada")

        self.session_token = self._extract_token(session_url)
        self.base_url = "https://kagi.com/images"

    def _get_session_url_from_env(self) -> str:
        """Obtém a URL de sessão do .env"""
        if url := os.environ.get("KAGI_SESSION_URL"):
            return url

        try:
            with open(".env") as f:
                for line in f:
                    if "=" in (line := line.strip()) and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        if key.strip() == "KAGI_SESSION_URL":
                            return value.strip().strip('"').strip("'")
        except FileNotFoundError:
            pass
        return None

    def _extract_token(self, url: str) -> str:
        """Extrai o token da URL de sessão"""
        params = parse_qs(urlparse(url).query)
        return params.get("token", [None])[0]

    def search_and_download(
        self,
        query: str,
        num_images: int = 10,
        size: str = None,
        output_dir: str = None,
        debug: bool = False,
    ) -> dict:
        """
        Busca e baixa imagens do Kagi

        Args:
            query: Termo de busca (ex: "Mike Azevedo art")
            num_images: Número de imagens para baixar
            size: Filtro de tamanho (small, medium, large, wallpaper)
            output_dir: Diretório para salvar imagens (padrão: downloads/)
            debug: Se True, mostra informações de debug

        Returns:
            Dict com resultados do download
        """
        # Criar URL de busca
        params = {"q": query}
        if self.session_token:
            params["token"] = self.session_token
        if size:
            params["size"] = size
        search_url = f"{self.base_url}?{urlencode(params)}"

        if debug:
            print(f"🔍 URL de busca: {search_url}")

        # Extrair mais URLs do que necessário para compensar rejeitadas
        # Multiplicador: tentar 3x mais para garantir qualidade
        search_multiplier = 3
        image_urls = self._extract_image_urls(search_url, num_images * search_multiplier, debug)

        if not image_urls:
            return {
                "success": False,
                "query": query,
                "error": "Nenhuma imagem encontrada",
                "downloaded": 0,
                "files": [],
            }

        # Preparar diretório de saída
        output_path = Path(output_dir or f"downloads/{self._sanitize_filename(query)}")
        output_path.mkdir(parents=True, exist_ok=True)

        # Baixar imagens até ter a quantidade desejada de boa qualidade
        downloaded_files = []
        attempts = 0
        len(image_urls)

        if debug:
            print(f"   🎯 Meta: {num_images} imagens | Disponíveis: {len(image_urls)} URLs")

        for img_url in image_urls:
            if len(downloaded_files) >= num_images:
                break  # Já temos imagens suficientes

            attempts += 1
            try:
                filename = self._download_image(img_url, output_path, attempts, debug)
                if filename:
                    downloaded_files.append(filename)
                    if debug:
                        print(
                            f"   📊 Progresso: {len(downloaded_files)}/{num_images} imagens de qualidade"
                        )
            except Exception as e:
                if debug:
                    print(f"   ❌ Erro ao baixar imagem {attempts}: {e}")

        # Renomear arquivos para sequência correta
        if downloaded_files:
            self._renumber_files(downloaded_files, output_path, debug)

        return {
            "success": True,
            "query": query,
            "requested": num_images,
            "found": len(image_urls),
            "downloaded": len(downloaded_files),
            "total_fetched": len(downloaded_files),
            "attempts": attempts,
            "output_dir": str(output_path),
            "files": downloaded_files,
        }
    def _download_images(self, image_urls: list, output_dir: Path, num_images: int, debug: bool = False) -> tuple:
        """Método de compatibilidade para testes - baixa múltiplas imagens"""
        downloaded = []
        for idx, url in enumerate(image_urls[:num_images], 1):
            try:
                result = self._download_image(url, output_dir, idx, debug)
                if result:
                    downloaded.append(result["path"])
            except Exception:
                continue
        return len(downloaded), downloaded
    def _extract_image_urls(self, url: str, num_images: int, debug: bool = False) -> list:
        """Usa Selenium para extrair URLs das imagens"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
        except ImportError:
            print("❌ Selenium não instalado. Instale com: pip install selenium")
            return []

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )

        driver = None
        image_urls = []

        try:
            driver = webdriver.Chrome(options=options)
            driver.get(url)

            if debug:
                print("   ⏳ Carregando página de resultados...")

            time.sleep(3)  # Aguardar a página carregar

            # Scroll para carregar mais imagens
            last_height = driver.execute_script("return document.body.scrollHeight")
            for scroll_attempts in range(1, 6):  # max 5 scrolls
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if debug:
                    print(f"   📜 Scroll {scroll_attempts}/5")
                if new_height == last_height or len(image_urls) >= num_images:
                    break
                last_height = new_height

            # Extrair URLs das imagens
            # O Kagi geralmente usa tags <img> dentro de links
            img_elements = driver.find_elements(By.TAG_NAME, "img")

            if debug:
                print(f"   🖼️  Encontrados {len(img_elements)} elementos <img>")

            for img in img_elements:
                # Tentar pegar URL original (geralmente está no link pai ou atributo data)
                img_url = None

                # Método 1: Ver se está dentro de um link <a>
                try:
                    parent_link = img.find_element(By.XPATH, "..")
                    if parent_link.tag_name == "a":
                        href = parent_link.get_attribute("href")
                        # Se href é uma URL de imagem direta, usar ela
                        if href and any(
                            ext in href.lower()
                            for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]
                        ):
                            img_url = href
                except Exception:
                    pass

                # Método 2: Atributos alternativos (priorizar alta resolução)
                if not img_url:
                    # Priorizar atributos de alta qualidade primeiro
                    img_url = (
                        img.get_attribute("data-full")
                        or img.get_attribute("data-original")
                        or img.get_attribute("data-img-url")
                        or img.get_attribute("data-href")
                        or img.get_attribute("data-img")
                        or img.get_attribute("data-highres")
                        or img.get_attribute("data-src")
                        or img.get_attribute("src")  # fallback - pode ser thumbnail
                    )

                # Filtrar e adicionar
                if (
                    img_url
                    and img_url.startswith("http")
                    and "/favicon" not in img_url
                    and "logo" not in img_url.lower()
                    and "icon" not in img_url.lower()
                    and img_url not in image_urls
                ):
                    # Verificar se parece ser thumbnail muito pequeno pela URL
                    if not any(
                        size in img_url.lower() for size in ["thumb", "small", "50x50", "100x100"]
                    ):
                        image_urls.append(img_url)
                        if debug and len(image_urls) <= 3:
                            print(f"   ✅ Imagem {len(image_urls)}: {img_url[:80]}...")
                        if len(image_urls) >= num_images:
                            break

            if debug:
                print(f"   📊 Total de imagens únicas encontradas: {len(image_urls)}")

            # Salvar HTML para debug se necessário
            if debug:
                with open("debug_images.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("   📄 HTML salvo em debug_images.html")

        except Exception as e:
            if debug:
                print(f"   ❌ Erro no Selenium: {e}")
        finally:
            if driver:
                driver.quit()

        return image_urls

    def _download_image(self, url: str, output_dir: Path, index: int, debug: bool = False) -> dict:
        """Baixa uma imagem e salva no diretório. Retorna dict com path e tamanho"""
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            ext = self._get_file_extension(url, response.headers.get("Content-Type", ""))
            filename = f"temp_{index:04d}{ext}"  # Usar temp_ para indicar que é temporário
            filepath = output_dir / filename

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verificar se imagem é muito pequena (provável thumbnail)
            file_size_kb = filepath.stat().st_size / 1024
            if file_size_kb < 30:  # Menor que 30KB, provavelmente é thumbnail/icon
                if debug:
                    print(f"   ⚠️  Pulada (muito pequena): {filename} ({file_size_kb:.1f} KB)")
                filepath.unlink()  # Deletar arquivo
                return None

            if debug and file_size_kb > 500:  # Destacar imagens grandes
                print(f"   ✅ Baixada (grande!): {filename} ({file_size_kb:.1f} KB)")

            return {"path": str(filepath), "size_kb": file_size_kb}
        except Exception as e:
            if debug:
                print(f"   ❌ Erro ao baixar {url}: {e}")
            return None

    def _get_file_extension(self, url: str, content_type: str) -> str:
        """Determina extensão do arquivo"""
        ext_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
            "image/bmp": ".bmp",
        }
        if ext := ext_map.get(content_type.lower()):
            return ext
        path = urlparse(url).path.lower()
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"]:
            if path.endswith(ext):
                return ext
        return ".jpg"

    def _sanitize_filename(self, filename: str) -> str:
        """Remove caracteres inválidos do nome do arquivo"""
        for char in '<>:"/\\|?*':
            filename = filename.replace(char, "_")
        return filename.strip()

    def _select_best_images(
        self, downloaded_files: list, num_images: int, output_dir: Path, debug: bool = False
    ) -> list:
        """Seleciona as N maiores imagens (melhor qualidade) e deleta o resto"""
        if not downloaded_files:
            return []

        # Ordenar por tamanho (maior primeiro)
        sorted_files = sorted(downloaded_files, key=lambda x: x["size_kb"], reverse=True)

        # Pegar as N maiores
        best_files = sorted_files[:num_images]
        rejected_files = sorted_files[num_images:]

        if debug:
            print(f"\n   📊 Seleção de qualidade:")
            print(f"   ✅ Melhores {len(best_files)} imagens: {best_files[0]['size_kb']:.1f} KB (maior) até {best_files[-1]['size_kb']:.1f} KB")
            if rejected_files:
                print(f"   🗑️  Descartando {len(rejected_files)} imagens menores")

        # Deletar arquivos rejeitados
        for file_info in rejected_files:
            try:
                Path(file_info["path"]).unlink()
            except Exception:
                pass

        # Retornar apenas os paths dos melhores
        return [f["path"] for f in best_files]

    def _renumber_files(self, files: list, output_dir: Path, debug: bool = False) -> None:
        """Renumera arquivos baixados para sequência correta 001, 002, 003..."""
        if not files:
            return

        # Renomear de temp_XXXX para image_XXX
        for idx, filepath in enumerate(files, 1):
            old_path = Path(filepath)
            ext = old_path.suffix
            new_name = f"image_{idx:03d}{ext}"
            new_path = output_dir / new_name

            # Se já existe arquivo com esse nome, deletar (não deveria acontecer)
            if new_path.exists():
                new_path.unlink()

            old_path.rename(new_path)

        if debug:
            print(f"   🔄 Arquivos renumerados: {len(files)} imagens")


def get_arg_value(arg_name: str) -> str:
    """Obtém valor de um argumento da linha de comando"""
    try:
        idx = sys.argv.index(arg_name)
        return sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    except (ValueError, IndexError):
        return None


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python kagi_images.py <query> [num_images]")
        print('  python kagi_images.py "Mike Azevedo art" 20')
        print('  python kagi_images.py "landscapes" 10 --size large')
        print('  python kagi_images.py "cats" 5 --output ./my_cats --debug')
        print("\nOpções:")
        print("  --size SIZE       Tamanho: small, medium, large, wallpaper")
        print("  --output DIR      Diretório de saída (padrão: downloads/<query>)")
        print("  --debug           Mostrar informações detalhadas")
        sys.exit(0)

    # Parsear argumentos
    query = sys.argv[1]
    num_images = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 10
    size = get_arg_value("--size")
    output_dir = get_arg_value("--output")
    debug = "--debug" in sys.argv

    print(f"\n🖼️  Kagi Image Downloader\n🔍 Busca: {query}\n📊 Imagens: {num_images}")
    if size:
        print(f"📏 Tamanho: {size}")
    print()

    try:
        downloader = KagiImageDownloader()
        result = downloader.search_and_download(
            query=query, num_images=num_images, size=size, output_dir=output_dir, debug=debug
        )

        print("\n" + "=" * 70)
        if result["success"]:
            print("✅ Download concluído!")
            print(f"📁 Diretório: {result['output_dir']}")
            print(f"🖼️  URLs encontradas: {result['found']}")
            print(f"🔄 Tentativas de download: {result.get('attempts', 0)}")
            print(f"💾 Imagens de qualidade: {result['downloaded']}")

            if result["downloaded"] >= result["requested"]:
                print(f"🎉 Meta atingida: {result['downloaded']}/{result['requested']}")
            else:
                print(
                    f"⚠️  Foram baixadas {result['downloaded']} de {result['requested']} solicitadas"
                )
        else:
            print(f"❌ Erro: {result.get('error')}")
        print("=" * 70 + "\n")

    except ValueError as e:
        print(f"❌ Erro: {e}")
        print("\nConfigure KAGI_SESSION_URL no .env")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
