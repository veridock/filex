# xsl - Universal File Editor

[![PyPI version](https://badge.fury.io/py/xsl.svg)](https://badge.fury.io/py/xsl)
[![Python Support](https://img.shields.io/pypi/pyversions/xsl.svg)](https://pypi.org/project/xsl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/veridock/xsl/workflows/Tests/badge.svg)](https://github.com/veridock/xsl/actions)

🛠️ **Powerful CLI tool and Python library for editing XML, SVG, and HTML files using XPath and CSS selectors.**

## ✨ Features

- **🔍 XPath & CSS Selectors** - Precise element targeting and querying
- **📁 Multiple Formats** - Full support for XML, SVG, and HTML documents  
- **🌐 Local & Remote Files** - Edit files locally or fetch from URLs
- **📦 Data URI Extraction** - Extract and decode embedded content (PDFs, images, documents)
- **⚡ Multiple Interfaces** - CLI commands, interactive shell, and HTTP server
- **🖥️ Web Interface** - Modern browser-based editor with real-time API
- **🐍 Python API** - Full programmatic access for automation and integration
- **🔧 Extensible** - Plugin architecture for custom file processors

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install xsl

# Full installation with all features  
pip install xsl[full]

# Specific feature sets
pip install xsl[xpath]     # XPath support only
pip install xsl[css]       # CSS selectors only  
pip install xsl[remote]    # Remote file support only
pip install xsl[server]    # HTTP server support only
```

### CLI Usage

```bash
# Load and query files
xsl load example.svg
xsl query "//svg:text[@id='title']"
xsl set "//svg:text[@id='title']" "New Title"

# Extract embedded data
xsl extract "//svg:image/@xlink:href" --output document.pdf
xsl extract "//svg:image/@xlink:href" --info

# Interactive shell
xsl shell

# HTTP Server
xsl server --port 8082
```

### Python API

```python
from xsl import FileEditor

# Load and edit file
editor = FileEditor('example.svg')
editor.set_element_text("//svg:text[@id='title']", "New Title")
editor.save('modified.svg')

# Extract Data URI
result = editor.extract_data_uri("//svg:image/@xlink:href")
if 'error' not in result:
    print(f"Found {result['mime_type']} ({result['size']} bytes)")

# Work with remote files
remote_editor = FileEditor('https://example.com/diagram.svg')
elements = remote_editor.list_elements("//svg:*[@id]")
```

## 📖 Documentation

- **[CLI Reference](docs/cli.md)** - Complete command-line interface guide
- **[Python API](docs/api.md)** - Full API documentation with examples  
- **[Server Guide](docs/server.md)** - HTTP server setup and API reference
- **[XPath Examples](docs/xpath.md)** - Common XPath patterns and use cases
- **[Tutorials](docs/tutorials/)** - Step-by-step guides for common tasks

## 🎯 Use Cases

### 📊 **Extract Data from SVG Diagrams**
```bash
# Extract embedded PDF from technical diagram
xsl extract "//svg:image/@xlink:href" --output manual.pdf

# Get chart data from SVG
xsl query "//svg:foreignObject//script[@type='application/json']"
```

### 🔧 **Batch Update XML Configurations**
```bash
# Update database connections across config files
for config in configs/*.xml; do
  xsl set "//database/host" "new-server.com" "$config"
  xsl save "$config"
done
```

### 🌐 **Parse Web Pages for Data**
```bash
# Extract structured data from HTML
xsl query "//table[@id='data']//tr[@data-status='active']" page.html
xsl extract "//script[@type='application/json']" --output data.json
```

### 🔄 **Document Format Conversion**
```python
# Convert XML structure using XPath
from xsl import FileEditor

source = FileEditor('legacy.xml')
data = source.list_elements("//record")

target = FileEditor('template.xml')
for item in data:
    target.add_element("//records", "entry", item['text'], item['attributes'])
target.save('migrated.xml')
```

## 🔍 XPath Examples

### SVG Files
```bash
# Get all text elements
//svg:text

# Find elements by ID
//svg:*[@id='title']

# Extract Data URIs
//svg:image/@xlink:href[starts-with(., 'data:')]

# Get metadata
//svg:metadata
```

### XML Files  
```bash
# Find by attribute
//user[@type='admin']

# Text content search
//*[contains(text(), 'error')]

# Nested elements
//config//database//host
```

### HTML Files
```bash
# CSS class targeting
//div[@class='content']

# Form elements
//input[@type='checkbox'][@checked]

# JSON script tags
//script[@type='application/json']
```

## 🌐 HTTP Server API

Start the server:
```bash
xsl server --port 8082
```

### Direct Data URI Extraction
```bash
# Extract from remote file
curl "http://localhost:8082/api/extract?url=https://example.com/diagram.svg&xpath=//svg:image/@href"
```

### Full API Workflow
```bash
# Load file
curl -X POST http://localhost:8082/api/load \
  -H "Content-Type: application/json" \
  -d '{"file_path": "example.svg"}'

# Query elements  
curl -X POST http://localhost:8082/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "//svg:text", "type": "xpath"}'

# Update content
curl -X POST http://localhost:8082/api/update \
  -H "Content-Type: application/json" \
  -d '{"xpath": "//svg:text[@id=\"title\"]", "type": "text", "value": "Updated"}'

# Save changes
curl -X POST http://localhost:8082/api/save \
  -H "Content-Type: application/json" \
  -d '{"output_path": "modified.svg"}'
```

### Web Interface

Open `http://localhost:8082` in your browser for a full-featured web interface with:

- 📁 **File Management** - Load local files or remote URLs
- 🔍 **Interactive Queries** - Test XPath and CSS selectors with real-time results
- ✏️ **Visual Editing** - Modify elements through web forms
- 📦 **Data Extraction** - Extract and download embedded resources
- 📊 **Element Browser** - Navigate document structure visually

## 🧪 Examples and Testing

Generate example files:
```bash
xsl examples --dir ./test_files
```

This creates:
- `example.svg` - SVG with embedded Data URIs and metadata
- `example.xml` - XML database with users and file data  
- `example.html` - HTML with embedded SVG and JSON
- `USAGE_EXAMPLES.md` - Comprehensive usage guide

## ⚙️ Configuration

### Optional Dependencies

xsl works with basic XML support out of the box, but optional dependencies unlock additional features:

- **`lxml`** - Required for XPath queries and advanced XML processing
- **`beautifulsoup4`** - Enables CSS selectors for HTML files
- **`requests`** - Allows loading files from remote URLs

Install all features:
```bash
pip install xsl[full]
```

### Environment Variables

```bash
# Default server settings
export xsl_DEFAULT_PORT=8082
export xsl_DEFAULT_HOST=localhost

# Debug mode
export xsl_DEBUG=1
```

## 🔧 Development

### Setup Development Environment

```bash
git clone https://github.com/veridock/xsl.git
cd xsl

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --extras "full"

# Run tests
poetry run pytest

# Format code
poetry run black xsl/
poetry run isort xsl/
```

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=xsl --cov-report=html

# Specific test categories
poetry run pytest -m "not slow"  # Skip slow tests
poetry run pytest -m "integration"  # Only integration tests
```

### Code Quality

```bash
# Format and lint
poetry run black xsl/ tests/
poetry run isort xsl/ tests/
poetry run flake8 xsl/ tests/
poetry run mypy xsl/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run tests: `poetry run pytest`
5. Format code: `poetry run black xsl/`
6. Commit: `git commit -m 'Add amazing feature'`
7. Push: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 📋 Requirements

- **Python 3.8+**
- **Optional:** lxml, beautifulsoup4, requests (install with `[full]` extra)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [lxml](https://lxml.de/) for robust XML processing
- Uses [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- Powered by [Poetry](https://python-poetry.org/) for dependency management

## 📞 Support

- 📖 **Documentation:** [GitHub Wiki](https://github.com/veridock/xsl/wiki)
- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/veridock/xsl/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/veridock/xsl/discussions)
- 📧 **Email:** contact@veridock.com

---

**Made with ❤️ by the xsl team**