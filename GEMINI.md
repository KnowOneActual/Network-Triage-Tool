# Network Triage Tool - Gemini Project Context

Terminal-based network diagnostic tool (TUI) for professionals.
Cross-platform (macOS, Linux, Windows), mouse-supportive, non-blocking UI.
Python 3.11+, Textual (UI), Scapy, Netmiko, psutil, requests, speedtest-cli, python-nmap.

## 🏗 Architecture & Modules

### Core Application
- **Main Entry:** `network_triage.app:run` (mapped to `network-triage` command).
- **App Logic:** `src/network_triage/app.py` (Main `NetworkTriageApp` class).
- **OS Toolkits:** `src/network_triage/[macos|linux|windows]/network_toolkit.py` - Platform-specific implementations.
- **TCSS Styling:** `src/network_triage/triage.tcss`.

### Diagnostic Utilities (Phase 3)
- **DNS:** `src/shared/dns_utils.py`.
- **Latency/Ping:** `src/shared/latency_utils.py`.
- **Ports:** `src/shared/port_utils.py`.

### TUI Widget Foundation (Phase 4)
- **BaseWidget:** `src/tui/widgets/base.py` - Foundation for all Phase 4 widgets.
- **AsyncMixin:** `AsyncOperationMixin` for non-blocking operations via `work(thread=True)`.
- **Components:** `src/tui/widgets/components.py` - Reusable UI elements (ResultsWidget, etc.).
- **Specific Widgets:** `dns_resolver_widget.py`, `port_scanner_widget.py`.

## 🛠 Development & Engineering Mandates

### 1. Workflow
- **Research -> Strategy -> Execution** lifecycle.
- **Empirical Reproduction:** Reproduce bugs before fixing.
- **Verification:** Every change MUST be verified with tests and local builds.
- **Parallel Testing:** Full suite (~106 tests) is fast (< 1s); run frequently with `pytest`.

### 2. Code Standards
- **Python Convention:** Follow PEP 8 strictly.
- **Typing:** Maintain 100% type hints for all new code.
- **Indentation:** **4 spaces** for Python files.
- **TUI Responsiveness:** NEVER perform blocking network I/O in the main TUI thread. Use `@work(thread=True)` and `self.app.call_from_thread()` or `AsyncOperationMixin` patterns.
- **Error Handling:** Use `BaseWidget.display_error()` or `AsyncOperationMixin.handle_error()` for user-facing feedback.

### 3. Testing
- **Framework:** `pytest` with `pytest-mock`.
- **Coverage:** Aim for high coverage (current is ~94%).
- **Widget Tests:** New widgets require comprehensive unit and integration tests.

### 4. Build & Environment
- **Installation:** `pip install -e .` for development.
- **Dependencies:** Avoid adding new external dependencies unless strictly necessary (Phase 3 utilities use stdlib only where possible).

## 🚀 Key Commands
- **Run App:** `network-triage`
- **Run Tests:** `pytest`
- **Linting:** `ruff check .`
- **Formatting:** `ruff format .`
- **Security:** `bandit -c pyproject.toml -r src/`
- **Secret Scan:** `gitleaks` (integrated in CI)
- **Type Checking:** `mypy src/`
- **Spelling:** `codespell`
- **Audit:** `pip-audit`
- **Dependabot:** Weekly updates for Pip and GitHub Actions.

## 📅 Roadmap Context (Current Phase: 4.3)
- **Phase 4.4 (Planned):** Latency Analyzer widget.
- **Phase 4.5 (Planned):** Results history and export.
- **Phase 5 (Future):** Data visualization and cloud integration.
