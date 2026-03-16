# Running tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_kagi_simple.py -v

# Run with markers
pytest tests/ -m unit -v
```

# Code quality

```bash
# Format code with Black
black .

# Lint with Ruff
ruff check .

# Type check with MyPy
mypy .
```

# Pre-commit hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```
