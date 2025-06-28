# Universal File Converter System
# Usage: make [library] [from_format] [to_format] [input_file] [output_file]
# Example: make imagemagick jpg png input.jpg output.png

SHELL := /bin/bash
CONVERTER_DIR := ./converters
HELP_DIR := ./help
CONFIG_DIR := ./config

# Default output file generation
define generate_output
$(if $(5),$(5),$(basename $(4)).$(3))
endef

# Color definitions for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Help system
.PHONY: help list-libraries list-formats search benchmark validate format lint install-dev push publish
help:
	@echo -e "$(BLUE)Universal File Converter System$(NC)"
	@echo ""
	@echo "Available commands:"
	@echo "  help              - Show this help"
	@echo "  install           - Install the package in development mode"
	@echo "  install-dev       - Install development dependencies"
	@echo "  format            - Format code using black and isort"
	@echo "  lint              - Lint code using flake8 and mypy"
	@echo "  test              - Run tests with pytest"
	@echo "  list              - List all supported file extensions"
	@echo "  push              - Push changes to git (runs tests and linting first)"
	@echo "  publish           - Publish package to PyPI (creates git tag and pushes changes)"
	@echo "  check-conflicts   - Check format conversion conflicts"
	@echo ""
	@echo "Examples:"
	@echo "  make format       # Format the code"
	@echo "  make lint         # Run linters"
	@echo "  make test         # Run tests"
	@echo "  make push         # Push changes to git"
	@echo "  make publish      # Publish to PyPI"

# Conversion function
define convert_file
	@if [ ! -f "$(CONVERTER_DIR)/$(1).sh" ]; then \
		echo -e "$(RED)Error: Library $(1) not found$(NC)"; \
		exit 1; \
	fi; \
	if [ -z "$(word 1,$(2))" ] || [ -z "$(word 2,$(2))" ] || [ -z "$(word 3,$(2))" ]; then \
		echo -e "$(RED)Error: Missing arguments$(NC)"; \
		echo "Usage: make $(1) [from_format] [to_format] [input_file] [output_file]"; \
		exit 1; \
	fi; \
	FROM_FORMAT="$(word 1,$(2))"; \
	TO_FORMAT="$(word 2,$(2))"; \
	INPUT_FILE="$(word 3,$(2))"; \
	OUTPUT_FILE="$(call generate_output,$(1),$$FROM_FORMAT,$$TO_FORMAT,$$INPUT_FILE,$(word 4,$(2)))"; \
	echo -e "$(GREEN)Converting with $(1):$(NC) $$INPUT_FILE ($$FROM_FORMAT) -> $$OUTPUT_FILE ($$TO_FORMAT)"; \
	bash $(CONVERTER_DIR)/$(1).sh "$$FROM_FORMAT" "$$TO_FORMAT" "$$INPUT_FILE" "$$OUTPUT_FILE"
endef

# Install the package in development mode
install:
	@echo -e "$(BLUE)Installing text2file in development mode...$(NC)"
	poetry install
	@echo -e "\n$(GREEN)Installation complete! You can now use the 'text2file' command.$(NC)"

# Install development dependencies
install-dev:
	@echo -e "$(BLUE)Installing development dependencies...$(NC)"
	poetry add --container dev \
		"black>=22.3.0,<23.0.0" \
		"isort>=5.10.1,<6.0.0" \
		"flake8>=5.0.0,<6.0.0" \
		"mypy>=0.971,<1.0.0" \
		"pytest>=7.0.0,<8.0.0" \
		"pytest-cov>=3.0.0,<4.0.0"
	@echo -e "$(GREEN)Development dependencies installed!$(NC)"

# Format code using black and isort
format:
	@echo -e "$(BLUE)Formatting code...$(NC)"
	poetry run black src/ tests/
	poetry run isort src/ tests/
	@echo -e "$(GREEN)Formatting complete!$(NC)"

# Lint code using flake8 and mypy
lint:
	@echo -e "$(BLUE)Linting code...$(NC)"
	poetry run flake8 src/ tests/
	poetry run mypy src/ tests/
	@echo -e "$(GREEN)Linting complete!$(NC)"

# List all supported file extensions
list:
	@echo -e "$(BLUE)Supported file extensions:$(NC)"
	@poetry run python scripts/list_extensions.py | sort | xargs -n 1 echo "  - "

# Install dependencies
install-deps:
	@echo -e "$(BLUE)Installing converter dependencies...$(NC)"
	@bash $(CONFIG_DIR)/install_dependencies.sh

# Push changes to git after running tests and linting
push: test
	@echo -e "$(GREEN)✓ All tests and linting passed!$(NC)"
	@echo -e "\n$(BLUE)Staging changes...$(NC)"
	git add .
	@if git diff --cached --quiet; then \
		echo -e "$(YELLOW)No changes to commit.$(NC)"; \
	else \
		git commit -m "Update package"; \
	fi
	@echo -e "\n$(BLUE)Pushing to git...$(NC)"
	git push
	@echo -e "\n$(GREEN)✓ Changes pushed to git$(NC)"
	@echo -e "\n$(BLUE)Next steps:$(NC)"
	@echo -e "1. To publish a new version to PyPI, run 'make publish'"
	@echo -e "   This will:\n   - Update the version in pyproject.toml\n   - Create a git tag\n   - Build and publish the package"

# Publish the package to PyPI
publish:
	@echo -e "$(BLUE)Building and publishing package...$(NC)"
	poetry version patch
	git add pyproject.toml
	git commit -m "Bump version"
	git tag -a v$$(poetry version -s) -m "Version $$(poetry version -s)"
	git push --follow-tags
	poetry build
	poetry publish
	@echo -e "\n$(GREEN)✓ Package published to PyPI!$(NC)"

# Prevent make from interpreting arguments as targets
%:
	@:
