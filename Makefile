.PHONY: help install dev test lint clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install HIAI
	pip install -e .

dev: ## Install in development mode
	pip install -e ".[dev]"

test: ## Run tests
	python3 -m unittest discover -s tests -v

lint: ## Run linting
	@command -v ruff >/dev/null 2>&1 && ruff check src/ tests/ || echo "Install ruff: pip install ruff"

format: ## Format code
	@command -v ruff >/dev/null 2>&1 && ruff format src/ tests/ || echo "Install ruff: pip install ruff"

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

check: ## Run all checks (lint + test)
	$(MAKE) lint
	$(MAKE) test
