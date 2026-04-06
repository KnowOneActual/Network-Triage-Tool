# Developer Guide for Network Triage Tool

## Modern Development Workflow

This guide outlines the modern development workflow using uv, pre-commit, and other 2024/2025 Python ecosystem tools.

## Prerequisites

### Required Tools
- **Python 3.12+** (3.14.3 recommended)
- **uv** (Ultra-fast Python package manager)
- **Docker** (optional, for containerized development)
- **Git** (version control)

### Install uv
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/knowoneactual/Network-Triage-Tool.git
cd Network-Triage-Tool

# Create virtual environment and install dependencies
uv venv
uv sync --all-extras

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Pre-commit Hooks
```bash
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

### 3. Run the Application
```bash
# Development mode
uv run network-triage

# With specific Python version
uv run --python 3.14 network-triage
```

## Development Commands

### Package Management with uv
```bash
# Install all dependencies (including dev)
uv sync --all-extras

# Install only runtime dependencies
uv sync

# Add a new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade

# Generate lock file
uv lock

# Check for outdated packages
uv pip list --outdated
```

### Code Quality
```bash
# Run all checks
uv run all

# Linting with ruff
uv run lint
uv run ruff check . --fix
uv run ruff format .

# Type checking with mypy
uv run type
uv run mypy src/

# Security scanning
uv run security
uv run bandit -r src/

# Spell checking
uv run spell
uv run codespell .
```

### Testing
```bash
# Run all tests
uv run test

# Run tests with coverage
uv run test-cov

# Run specific test file
uv run pytest tests/test_phase4_foundation.py -v

# Run single test
uv run pytest tests/test_phase4_foundation.py::TestBaseWidget::test_base_widget_initialization

# Run tests with markers
uv run pytest -m "not slow"  # Skip slow tests
uv run pytest -m "network"   # Run only network tests

# Generate coverage report
uv run pytest --cov=src --cov-report=html
```

### Development Tools
```bash
# Interactive Python shell
uv run ipython

# Debug with pdb
uv run python -m pdb -m network_triage.app

# Watch for file changes and run tests
uv run ptw -- -v

# Benchmark performance
uv run pytest --benchmark-only
```

## Docker Development

### Using Docker Compose
```bash
# Start development environment
docker-compose up dev

# Run tests in container
docker-compose run --rm test

# Run linter in container
docker-compose run --rm lint

# Run type checker in container
docker-compose run --rm type

# Build production image
docker-compose build prod
```

### Manual Docker Commands
```bash
# Build development image
docker build -t network-triage:dev --target dev .

# Run development container
docker run -it --rm \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/tests:/app/tests \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  --privileged \
  network-triage:dev

# Build production image
docker build -t network-triage:latest .

# Run production container
docker run -it --rm \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  --privileged \
  network-triage:latest
```

## Git Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `fix/*`: Bug fixes
- `docs/*`: Documentation updates

### Commit Convention
Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat(widgets): add port scanner widget with concurrent scanning
fix(dns): handle IPv6 resolution errors gracefully
test(latency): add comprehensive ping statistics tests
docs(readme): update installation instructions for uv
chore(deps): update ruff to 0.15.5
refactor(utils): simplify error handling with match statements
```

### Pre-commit Hooks
Pre-commit hooks automatically run on `git commit`:
- Code formatting with ruff
- Linting with ruff
- Type checking with mypy
- Security scanning with bandit
- Spell checking with codespell
- Secret detection with gitleaks
- Commit message validation

To skip pre-commit hooks:
```bash
git commit --no-verify -m "Emergency fix"
```

## Code Style Guidelines

### Python 3.14 Features
- Use **match statements** instead of long if/elif chains
- Use **type hints** for all function parameters and return values
- Use **dataclasses** or **Pydantic models** for data structures
- Use **async/await** for I/O-bound operations
- Use **f-strings** for string formatting

### Import Organization
```python
# 1. Standard library imports
import datetime
import sys
from pathlib import Path

# 2. Third-party imports
import pytest
from textual.app import App
from textual.widgets import Button, Label

# 3. Local imports
from tui.widgets.base import BaseWidget
from .models import NetworkResult
```

### Error Handling
```python
from typing import Optional
from dataclasses import dataclass

@dataclass
class OperationResult:
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    
    @classmethod
    def from_exception(cls, exc: Exception) -> "OperationResult":
        return cls(success=False, error=str(exc))

def perform_operation() -> OperationResult:
    try:
        result = do_something()
        return OperationResult(success=True, data=result)
    except ConnectionError as e:
        return OperationResult.from_exception(e)
    except TimeoutError:
        return OperationResult(success=False, error="Operation timed out")
```

### Testing Patterns
```python
import pytest
from unittest.mock import Mock, patch
from typing import AsyncGenerator

@pytest.fixture
async def test_widget() -> AsyncGenerator[BaseWidget, None]:
    """Async fixture for widget testing."""
    widget = TestWidget()
    yield widget
    await widget.cleanup()

@pytest.mark.asyncio
async def test_async_operation(test_widget: BaseWidget):
    """Test async operation with proper cleanup."""
    result = await test_widget.async_operation("test")
    assert result.success
    assert "test" in result.data

def test_with_mocks():
    """Test with mocked dependencies."""
    with patch("socket.gethostbyname") as mock_gethost:
        mock_gethost.return_value = "192.168.1.1"
        result = resolve_hostname("localhost")
        assert result.ipv4_addresses == ["192.168.1.1"]
```

## Performance Optimization

### Profiling
```bash
# Profile CPU usage
uv run python -m cProfile -o profile.stats -m network_triage.app

# Analyze profile
uv run python -m pstats profile.stats

# Memory profiling
uv run python -m memory_profiler src/network_triage/app.py

# Line-by-line profiling
uv run kernprof -l -v src/network_triage/app.py
```

### Async Optimization
```python
import asyncio
from typing import List

async def concurrent_operations(items: List[str]) -> List[str]:
    """Run operations concurrently."""
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

## Troubleshooting

### Common Issues

**1. uv not found**
```bash
# Add uv to PATH
export PATH="$HOME/.cargo/bin:$PATH"
# or reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Pre-commit hooks failing**
```bash
# Run pre-commit manually
uv run pre-commit run --all-files

# Skip specific hook
uv run pre-commit run ruff --files src/network_triage/app.py
```

**3. Docker network permissions**
```bash
# Run with elevated privileges
docker run --cap-add=NET_ADMIN --cap-add=NET_RAW --privileged
```

**4. Type checking errors**
```bash
# Check specific file
uv run mypy src/shared/dns_utils.py

# Generate type stubs
uv run stubgen src/network_triage/
```

### Debugging Tips
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uv run network-triage

# Run with pdb
uv run python -m pdb -m network_triage.app

# Check dependencies
uv pip list --format=freeze
```

## CI/CD Integration

### GitHub Actions Example
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --all-extras
      - run: uv run all
      - run: uv run test-cov
```

## Resources

### Documentation
- [uv Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Textual Documentation](https://textual.textualize.io/)
- [Python 3.14 Documentation](https://docs.python.org/3.14/)

### Tools
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- [ruff](https://github.com/astral-sh/ruff) - Fast Python linter and formatter
- [pre-commit](https://pre-commit.com/) - Git hook manager
- [pytest](https://docs.pytest.org/) - Testing framework

### Best Practices
- [Python Packaging User Guide](https://packaging.python.org/)
- [Hypermodern Python](https://cjolowicz.github.io/posts/hypermodern-python-01-setup/)
- [Python Type Checking](https://realpython.com/python-type-checking/)

---

*Last Updated: $(date)*
*For questions, open an issue or check the [AGENTS.md](AGENTS.md) file.*