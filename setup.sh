#!/bin/bash
# xsl Setup Script
# Automated setup for xsl development environment

set -e

echo "🚀 Setting up xsl development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    print_error "pyproject.toml not found. Make sure you're in the xsl root directory."
    exit 1
fi

print_status "Found pyproject.toml, continuing setup..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    print_error "Python 3.8+ required. Found: Python $python_version"
    exit 1
fi

print_status "Python version check passed: $python_version"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    print_warning "Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add Poetry to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry installation failed. Please install manually."
        print_info "Visit: https://python-poetry.org/docs/#installation"
        exit 1
    fi
fi

print_status "Poetry is available"

# Install dependencies
print_info "Installing dependencies with Poetry..."
poetry install --extras "full"

if [[ $? -eq 0 ]]; then
    print_status "Dependencies installed successfully"
else
    print_error "Dependency installation failed"
    exit 1
fi

# Create necessary directories
print_info "Creating project directories..."
mkdir -p docs tests/fixtures scripts

print_status "Project directories created"

# Generate example files
print_info "Creating example files..."
poetry run python -c "
from xsl.examples import create_example_files
try:
    files = create_example_files('tests/fixtures')
    print(f'Created {len(files)} example files')
    for f in files:
        print(f'  - {f}')
except Exception as e:
    print(f'Error creating examples: {e}')
"

if [[ $? -eq 0 ]]; then
    print_status "Example files created"
else
    print_warning "Could not create example files (will be created during tests)"
fi

# Run basic tests to verify installation
print_info "Running basic tests..."
poetry run python -c "
import xsl
print(f'xsl version: {xsl.__version__}')

# Test basic functionality
from xsl import FileEditor
print('✓ FileEditor import successful')

# Check capabilities
capabilities = xsl.get_capabilities()
print(f'✓ Available capabilities: {capabilities}')

deps = xsl.check_dependencies()
print('Dependencies:')
for dep, available in deps.items():
    status = '✓' if available else '✗'
    print(f'  {status} {dep}: {available}')
"

if [[ $? -eq 0 ]]; then
    print_status "Basic functionality test passed"
else
    print_error "Basic functionality test failed"
    exit 1
fi

# Run full test suite
print_info "Running test suite..."
poetry run pytest --tb=short -v

if [[ $? -eq 0 ]]; then
    print_status "All tests passed"
else
    print_warning "Some tests failed, but setup completed"
fi

# Print setup summary
echo ""
echo "🎉 xsl setup completed successfully!"
echo ""
print_info "What's installed:"
echo "  📦 xsl package with all dependencies"
echo "  🧪 Test suite and example files"
echo "  🔧 Development tools (black, isort, mypy, pytest)"
echo ""
print_info "Next steps:"
echo "  🚀 Try the CLI: poetry run xsl --help"
echo "  🌐 Start server: poetry run xsl server --port 8082"
echo "  🐍 Use Python API: poetry run python -c 'from xsl import FileEditor; print(\"Ready!\")'"
echo "  📝 Run shell: poetry run xsl shell"
echo ""
print_info "Development commands:"
echo "  🧪 Run tests: poetry run pytest"
echo "  🎨 Format code: poetry run black xsl/ && poetry run isort xsl/"
echo "  🔍 Type check: poetry run mypy xsl/"
echo "  📦 Build package: poetry build"
echo ""
print_info "Documentation:"
echo "  📖 README.md - Main documentation"
echo "  📁 tests/fixtures/ - Example files for testing"
echo "  🌐 Start server and visit http://localhost:8082 for web interface"
echo ""

# Check if we're in a git repository
if [[ -d ".git" ]]; then
    print_info "Git repository detected. Consider setting up pre-commit hooks:"
    echo "  poetry run pre-commit install"
else
    print_warning "Not in a git repository. Initialize with: git init"
fi

print_status "Setup complete! Happy coding! 🎯"