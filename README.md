# Skrypty i komendy setup dla xsl

## 🚀 Inicjalizacja projektu

### 1. Klonowanie repozytorium
```bash
git clone git@github.com:veridock/xsl.git
cd xsl
```

### 2. Setup Poetry i dependencies
```bash
# Zainstaluj Poetry (jeśli nie masz)
curl -sSL https://install.python-poetry.org | python3 -

# Lub przez pip
pip install poetry

# Zainstaluj dependencies
poetry install

# Instalacja z wszystkimi dodatkami
poetry install --extras "full"
```

### 3. Inicjalizacja struktur katalogów
```bash
# Utwórz wszystkie potrzebne katalogi
mkdir -p xsl tests docs scripts tests/fixtures

# Skopiuj pliki testowe
poetry run python scripts/create_examples.py --dir tests/fixtures
```

## 📝 Pliki które musisz utworzyć

### xsl/editor.py
```python
# Skopiuj z głównego artifact file_editor_tool 
# klasy FileEditor i powiązane
```

### xsl/cli.py  
```python
# Skopiuj z głównego artifact file_editor_tool
# klasę CLI i funkcję main
```

### xsl/server.py
```python
# Skopiuj z głównego artifact file_editor_tool  
# klasę FileEditorServer i funkcję main dla serwera
```

### LICENSE
```
MIT License

Copyright (c) 2025 xsl Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Testing
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
*.backup
*.tmp
test_output/
examples/output/
```

## 🧪 Development commands

### Testy
```bash
# Uruchom wszystkie testy
poetry run pytest

# Testy z coverage
poetry run pytest --cov=xsl --cov-report=html

# Tylko szybkie testy (bez slow)
poetry run pytest -m "not slow"

# Testy z output
poetry run pytest -v -s
```

### Code quality
```bash
# Formatowanie
poetry run black xsl/ tests/
poetry run isort xsl/ tests/

# Linting
poetry run flake8 xsl/ tests/

# Type checking
poetry run mypy xsl/
```

### Build i publikacja
```bash
# Build package
poetry build

# Check package
poetry run twine check dist/*

# Publish to PyPI (po skonfigurowaniu credentials)
poetry publish

# Publish to Test PyPI
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi
```

## 📚 Development workflow

### 1. Nowa funkcjonalność
```bash
# Utwórz branch
git checkout -b feature/nowa-funkcjonalność

# Zrób zmiany
# Dodaj testy
# Uruchom testy
poetry run pytest

# Format code
poetry run black xsl/
poetry run isort xsl/

# Commit i push
git add .
git commit -m "Add: nowa funkcjonalność"
git push origin feature/nowa-funkcjonalność
```

### 2. Przed release
```bash
# Aktualizuj wersję w pyproject.toml
# Aktualizuj CHANGELOG.md
# Uruchom wszystkie testy
poetry run pytest

# Build i sprawdź
poetry build
poetry run twine check dist/*

# Tag i push
git tag v0.1.0
git push origin v0.1.0
```

## 🔧 Dodatkowe skrypty

### scripts/create_examples.py
```python
#!/usr/bin/env python3
"""Create example files for testing and documentation."""

import argparse
from pathlib import Path

def create_examples(output_dir: str):
    """Create example XML/SVG/HTML files."""
    # Implementacja z głównego narzędzia
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="examples")
    args = parser.parse_args()
    create_examples(args.dir)
```

### scripts/benchmark.py  
```python
#!/usr/bin/env python3
"""Benchmark xsl performance."""

import time
from xsl import FileEditor

def benchmark_xpath_queries():
    """Benchmark XPath query performance."""
    # Implementacja benchmarków
    pass

if __name__ == "__main__":
    benchmark_xpath_queries()
```

## 📋 Checklist przed publikacją

- [ ] Wszystkie testy przechodzą
- [ ] Code coverage > 80%
- [ ] Dokumentacja zaktualizowana
- [ ] CHANGELOG.md zaktualizowany
- [ ] Wersja w pyproject.toml zaktualizowana
- [ ] README.md kompletny z przykładami
- [ ] LICENSE plik dodany
- [ ] .gitignore skonfigurowany
- [ ] CI/CD skonfigurowane (GitHub Actions)
- [ ] Package zbudowany i sprawdzony
- [ ] Tag git utworzony

## 🌐 CI/CD z GitHub Actions

### .github/workflows/test.yml
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Install dependencies
      run: poetry install --extras "full"
    
    - name: Run tests
      run: poetry run pytest --cov=xsl --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

### .github/workflows/publish.yml
```yaml
name: Publish

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Build package
      run: poetry build
    
    - name: Publish to PyPI
      env:
        POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
      run: poetry publish
```

## 📖 Użycie po instalacji

```bash
# Zainstaluj z PyPI
pip install xsl[full]

# Użyj CLI
xsl load example.svg
xsl query "//svg:text"
xsl server --port 8080

# Użyj w Python
python -c "from xsl import FileEditor; print('Works!')"
```


🛠️ Powerful CLI tool and library for editing XML, SVG, and HTML files using XPath and CSS selectors.

## ✨ Features

- **XPath & CSS Selectors** - Precise element targeting
- **Multiple Formats** - XML, SVG, HTML support  
- **Local & Remote Files** - Edit files locally or from URLs
- **Data URI Extraction** - Extract and decode embedded content (PDFs, images)
- **Multiple Interfaces** - CLI commands, interactive shell, HTTP server
- **Web Interface** - Browser-based editor with API

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install xsl

# Full installation with all features
pip install xsl[full]

# Specific features
pip install xsl[xpath]     # XPath support
pip install xsl[css]       # CSS selectors  
pip install xsl[remote]    # Remote file support

[XPath File Editing CLI Tool - Claude](https://claude.ai/chat/c8910e64-c97a-448f-bee7-7b6237b8145f)

> ### Usage
> 
> bash
> 
>     # CLI Commands
>     xsl load example.svg
>     xsl query "//svg:text[@id='title']"
>     xsl set "//svg:text[@id='title']" "New Title"
>     xsl extract "//svg:image/@xlink:href" --output document.pdf
>     xsl save --output modified.svg
>     
>     # Interactive Shell
>     xsl shell
>     
>     # HTTP Server
>     xsl server --port 8080
> 
> ### Python API
> 
> python
> 
>     from xsl import FileEditor
>     
>     # Load and edit file
>     editor = FileEditor('example.svg')
>     editor.set_element_text("//svg:text[@id='title']", "New Title")
>     editor.save('modified.svg')
>     
>     # Extract Data URI
>     result = editor.extract_data_uri("//svg:image/@xlink:href")
>     print(f"Found {result['mime_type']} ({result['size']} bytes)")
> 
> ## 📖 Documentation
> 
> -   [CLI Reference](https://claude.ai/chat/docs/cli.md)
> -   [API Documentation](https://claude.ai/chat/docs/api.md)
> -   [Examples](https://claude.ai/chat/docs/examples.md)
> 
> ## 🤝 Contributing
> 
> 1.  Fork the repository
> 2.  Create feature branch (`git checkout -b feature/amazing-feature`)
> 3.  Commit changes (`git commit -m 'Add amazing feature'`)
> 4.  Push to branch (`git push origin feature/amazing-feature`)
> 5.  Open Pull Request



Teraz stworzę jeszcze kilka kluczowych plików dla kompletnego pakietu:## 🎉 **Kompletny pakiet xsl gotowy!**

Stworzyłem kompletną strukturę pakietu Poetry dla repozytorium `git@github.com:veridock/xsl.git` z następującymi komponentami:

### 📁 **Struktura plików:**
```
xsl/
├── pyproject.toml              # ✅ Poetry konfiguracja
├── README.md                   # ✅ Dokumentacja
├── LICENSE                     # ✅ MIT License
├── .gitignore                  # ✅ Git ignore rules
├── xsl/
│   ├── __init__.py            # ✅ Package init z auto-detection
│   ├── editor.py              # 📝 Do skopiowania z głównego narzędzia
│   ├── cli.py                 # 📝 Do skopiowania z głównego narzędzia  
│   ├── server.py              # 📝 Do skopiowania z głównego narzędzia
│   └── utils.py               # ✅ Funkcje pomocnicze
├── tests/
│   ├── test_editor.py         # ✅ Kompletne testy jednostkowe
│   └── fixtures/              # 📁 Pliki testowe
└── docs/                       # 📁 Dokumentacja
```

### 🚀 **Instrukcje setup:**

1. **Klonuj repo i inicjalizuj:**
```bash
git clone git@github.com:veridock/xsl.git
cd xsl
poetry install --extras "full"
```

2. **Skopiuj kod z głównego narzędzia:**
   - Z artifact `file_editor_tool` skopiuj klasę `FileEditor` do `xsl/editor.py`
   - Klasę `CLI` do `xsl/cli.py`  
   - Klasę `FileEditorServer` do `xsl/server.py`

3. **Uruchom testy:**
```bash
poetry run pytest
```

4. **Build i publish:**
```bash
poetry build
poetry publish
```

### ⭐ **Kluczowe funkcjonalności pakietu:**

- **Opcjonalne dependencies** - `pip install xsl[full]` dla wszystkich funkcji
- **CLI commands** - `xsl` i `xsl-server` jako executables  
- **Python API** - `from xsl import FileEditor`
- **Kompletne testy** - z pytest, coverage, fixtures
- **Type hints** - mypy support
- **Code quality** - black, isort, flake8
- **CI/CD ready** - GitHub Actions workflows
- **PyPI ready** - wszystkie metadane skonfigurowane

### 🎯 **Po instalacji użytkownicy będą mogli:**

```bash
# Instalacja
pip install xsl[full]

# CLI usage  
xsl load example.svg
xsl extract "//svg:image/@xlink:href" --output doc.pdf
xsl server --port 8080

# Python API
from xsl import FileEditor
editor = FileEditor('file.svg')
editor.extract_data_uri("//svg:image/@xlink:href")
```

