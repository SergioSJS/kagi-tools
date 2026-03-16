# Kagi Tools - Busca e Resumo Integrados

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue)](/.github/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Ferramentas para usar o Kagi Search e Summarizer com sessão autenticada.

## 🚀 Instalação

### Pré-requisitos

1. **Python 3.11+** instalado no sistema
   - macOS: `brew install python@3.11` ou baixe de [python.org](https://www.python.org/downloads/)
   - Linux: `sudo apt install python3.11` ou equivalente
   - Windows: Baixe de [python.org](https://www.python.org/downloads/)

2. **UV** - Gerenciador de pacotes Python ultrarrápido
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Ou via pip
   pip install uv
   ```

### Instalação das Dependências

```bash
# 1. Criar ambiente virtual
uv venv

# 2. Ativar ambiente virtual
source .venv/bin/activate  # macOS/Linux
# ou
.venv\Scripts\activate     # Windows

# 3. Instalar dependências
uv pip install -r requirements.txt
```

**Nota:** ChromeDriver é necessário para o Selenium (resumo de páginas):
- macOS: `brew install chromedriver`
- Linux: `sudo apt install chromium-chromedriver`
- Windows: Baixe de [chromedriver.chromium.org](https://chromedriver.chromium.org/)

## ⚙️ Configuração

1. Copie o arquivo de exemplo:
   ```bash
   cp .env.example .env
   ```

2. Faça login no [Kagi](https://kagi.com)

3. Faça uma busca qualquer

4. Copie a URL completa da barra de endereços

5. Edite o arquivo `.env` e adicione sua URL:
   ```bash
   KAGI_SESSION_URL=https://kagi.com/search?token=seu-token-aqui
   ```

**⚠️ Importante:** Nunca compartilhe seu arquivo `.env` - ele contém seu token de sessão!

## � Uso Rápido

```bash
# 1. Ativar ambiente virtual
source .venv/bin/activate

# 2. Fazer uma busca simples
python kagi_simple.py 'python tutorial'

# 3. Busca com resumo integrado
python kagi_integrated.py 'machine learning' --qtd 3 --resumo
```

## �📚 Uso Principal

### Função Integrada (Busca + Resumo)

```python
from kagi_integrated import kagi_search_with_summary

# Busca simples
results = kagi_search_with_summary(
    query="python tutorial",
    qtd=3
)

# Busca com resumo
results = kagi_search_with_summary(
    query="machine learning",
    qtd=2,
    resumo=True,
    idioma="PT"
)
```

**Via CLI:**
```bash
# Certifique-se de ativar o ambiente virtual primeiro
source .venv/bin/activate

# Busca básica
python kagi_integrated.py 'python tutorial'

# Com mais resultados
python kagi_integrated.py 'AI news' --qtd 5

# Com resumo
python kagi_integrated.py 'climate change' --qtd 2 --resumo

# Resumo em inglês
python kagi_integrated.py 'AI news' --qtd 3 --resumo --lang EN
```

### Apenas Busca

```bash
python kagi_simple.py 'sua busca aqui'
python kagi_simple.py 'python tutorial' --debug
```

### Apenas Resumo

```bash
python kagi_summarizer.py 'https://example.com/article'
python kagi_summarizer.py 'https://example.com' --lang EN --type takeaway
```

## 📊 Formato de Retorno

```json
[
  {
    "idx": 1,
    "url": "https://docs.python.org/3/tutorial/",
    "title": "The Python Tutorial",
    "snippet": "Descrição curta do resultado",
    "summary": "Resumo completo gerado pelo Kagi (se resumo=True)",
    "summary_error": null
  }
]
```

## 📁 Estrutura de Arquivos

**Principais:**
- `kagi_integrated.py` - Busca + Resumo integrado
- `kagi_simple.py` - Busca no Kagi
- `kagi_summarizer.py` - Resumo de URLs
- `.env` - Configuração da sessão

**Extras:**
- `tests/` - Arquivos de teste
- `backup_files/` - Backups e arquivos antigos
- `requirements.txt` - Dependências

## ⚙️ Opções Avançadas

### Engines do Summarizer

```bash
# Mais rápido
--engine cecil

# Mais completo
--engine agnes

# Balanceado
--engine daphne

# Focado
--engine muriel
```

### Tipos de Resumo

```bash
# Resumo padrão
--type summary

# Pontos principais
--type takeaway
```

## 🔧 Troubleshooting

**Erro de sessão:** 
- Verifique se a URL no `.env` está atualizada
- Faça login novamente no Kagi e pegue uma nova URL

**Selenium não encontrado:**
```bash
pip install selenium
```

**ChromeDriver não encontrado:**
- O Selenium 4+ gerencia automaticamente
- Apenas certifique-se de ter Chrome instalado

## Como Usar

### Executar os testes:

```bash
python test_kagi.py
```

### Usar o CLI diretamente:

```bash
# Busca simples
python kagi_search.py "python programming"

# Limitar número de resultados
python kagi_search.py "machine learning" -n 5

# Saída em JSON
python kagi_search.py "artificial intelligence" --json

# Sem buscas relacionadas
python kagi_search.py "climate change" --no-related

# Paginação
python kagi_search.py "data science" -n 5 -s 5
```

## Estrutura dos Arquivos

- `kagi_search.py` - Script principal com a implementação da busca
- `test_kagi.py` - Exemplos de teste
- `.env.example` - Exemplo de configuração
- `README.md` - Este arquivo

## Testes Disponíveis

No arquivo `test_kagi.py`, você encontrará:

1. **test_simple_search()** - Busca básica com formatação
2. **test_json_output()** - Saída em formato JSON
3. **test_pagination()** - Teste de paginação de resultados
4. **test_with_related()** - Busca com sugestões relacionadas

Descomente os testes que deseja executar na função `main()`.


## 🧪 Desenvolvimento e Testes

### Executar Testes

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências de desenvolvimento
uv pip install -e ".[dev]" --python .venv/bin/python

# Rodar todos os testes
pytest tests/ -v

# Rodar com cobertura
pytest tests/ --cov=. --cov-report=html
```

### Qualidade de Código

```bash
# Formatar código
black .

# Verificar lint
ruff check .

# Type checking
mypy . --ignore-missing-imports
```

### Pre-commit Hooks

```bash
# Instalar hooks
pre-commit install

# Rodar manualmente
pre-commit run --all-files
```

Consulte [TESTING.md](TESTING.md) para mais detalhes sobre testes.

## 📜 Licença

Este projeto é de código aberto e está disponível sob a licença MIT.
