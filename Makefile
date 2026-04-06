# Network Triage Tool - Makefile
# Common development commands for faster workflow

.PHONY: help install test lint format type-check security clean build run dev setup check-all

# Default target
help:
	@echo "Network Triage Tool Development Commands"
	@echo "========================================"
	@echo "install     - Install dependencies with uv"
	@echo "test        - Run tests with pytest"
	@echo "lint        - Run ruff linter"
	@echo "format      - Format code with ruff"
	@echo "type-check  - Run mypy type checking"
	@echo "security    - Run security checks with bandit"
	@echo "check-all   - Run all quality checks"
	@echo "clean       - Clean build artifacts"
	@echo "build       - Build package"
	@echo "run         - Run the application"
	@echo "dev         - Run in development mode"
	@echo "setup       - Complete development setup"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies with uv..."
	uv sync --all-extras

# Run tests
test:
	@echo "Running tests..."
	uv run pytest tests/ -v

test-coverage:
	@echo "Running tests with coverage..."
	uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=45

test-specific:
	@echo "Running specific test pattern: $(filter-out $@,$(MAKECMDGOALS))"
	uv run pytest -k "$(filter-out $@,$(MAKECMDGOALS))" -v

# Linting
lint:
	@echo "Running ruff linter..."
	uv run ruff check .

lint-fix:
	@echo "Running ruff linter with auto-fix..."
	uv run ruff check --fix .

# Formatting
format:
	@echo "Formatting code with ruff..."
	uv run ruff format .

# Type checking
type-check:
	@echo "Running mypy type checking..."
	uv run mypy src/

# Security checks
security:
	@echo "Running security checks..."
	uv run bandit -r src/ -c pyproject.toml

# Spell checking
spell:
	@echo "Running spell check..."
	uv run codespell .

# Run all quality checks
check-all: lint type-check security test-coverage
	@echo "All quality checks passed! ✅"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Build package
build:
	@echo "Building package..."
	uv run python -m build

# Run the application
run:
	@echo "Running Network Triage Tool..."
	uv run network-triage

# Development mode (with reload)
dev:
	@echo "Running in development mode..."
	NETWORK_TRIAGE_DEBUG=true uv run network-triage

# Complete development setup
setup: install
	@echo "Setting up pre-commit hooks..."
	uv run pre-commit install
	@echo "Development setup complete! 🎉"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env and adjust settings"
	@echo "2. Run 'make check-all' to verify everything works"
	@echo "3. Run 'make dev' to start the application"

# Pre-commit hooks
pre-commit:
	@echo "Running pre-commit hooks..."
	uv run pre-commit run --all-files

pre-commit-install:
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker build -t network-triage .

docker-run:
	@echo "Running Docker container..."
	docker run -it --rm --cap-add=NET_ADMIN --cap-add=NET_RAW --privileged network-triage

docker-compose-up:
	@echo "Starting with docker-compose..."
	docker-compose up prod

# Helper for test-specific target
%:
	@:
