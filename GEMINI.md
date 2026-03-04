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
- **Parallel Testing:** Full suite (~184 items) is fast; run frequently with `pytest`.

### 2. Code Standards
- **Python Convention:** Follow PEP 8 strictly (enforced by Ruff).
- **Typing:** Maintain type hints for all new code (verified by Mypy).
- **Indentation:** **4 spaces** for Python files.
- **TUI Responsiveness:** NEVER perform blocking network I/O in the main TUI thread. Use `@work(thread=True)` and `self.app.call_from_thread()` or `AsyncOperationMixin` patterns.
- **Error Handling:** Use `BaseWidget.display_error()` or `AsyncOperationMixin.handle_error()` for user-facing feedback.

### 3. Testing
- **Framework:** `pytest` with `pytest-mock`.
- **Coverage:** Minimum 45% total coverage required (enforced by CI).
- **Widget Tests:** New widgets require comprehensive unit and integration tests.

### 4. Build & Environment
- **Installation:** `pip install -e .` for development.
- **Dependencies:** Avoid adding new external dependencies unless strictly necessary (Phase 3 utilities use stdlib only where possible).

## 🚀 Key Commands
- **Run App:** `network-triage`
- **Run Tests:** `pytest --cov`
- **Linting:** `ruff check .`
- **Formatting:** `ruff format .`
- **Type Checking:** `mypy src/`
- **Security:** `bandit -c pyproject.toml -r src/`
- **Spelling:** `codespell`
- **Audit:** `pip-audit`
- **Dependabot:** Weekly updates for Pip and GitHub Actions.

## 📅 Roadmap Context (Current Phase: 4.3)
- **Phase 4.4 (Next):** Live Path Analyzer (MTR-style) with live latency/loss per hop.
- **Phase 4.5 (Planned):** Connection Monitor (Active TCP/UDP sockets and processes).
- **Phase 4.6 (Planned):** LAN Bandwidth Tester (Iperf3-lite client).
- **Phase 5 (Future):** Traffic Health (Broadcast traffic counters).

## 🚫 Architectural Exclusions
- **No Deep Packet Inspection:** We focus on counters/summaries, not full Wireshark-style viewing.
- **No Heavy Scanning:** No aggressive Nmap NSE scripts or OS fingerprinting by default.
- **No Heavy State:** Zero-config priority; no local database requirements.
