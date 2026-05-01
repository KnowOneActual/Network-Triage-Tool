# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.9] - 2026-05-01

### Added
- **Streaming Port Scanning** — Refactored Port Scanner to use async generators, enabling real-time UI updates as each port is checked.
- **Progressive Path Analysis** — Implemented streaming MTR-style path analysis that displays hops as they are discovered.
- **Async Subprocess Streaming** — Leveraged `asyncio.create_subprocess_exec` for non-blocking command execution in network utilities.

### Changed
- **Test Suite Updates** — Modernized functional tests for Port and Latency widgets to support streaming patterns.
- **Performance Optimization** — Optimized network operation concurrency with task-based streaming.

## [0.5.8] - 2026-04-23

### Added
- **Phase 4.6: LAN Bandwidth Tester** — Integrated iperf3-lite style throughput monitoring with real-time RX/TX display.
- **Phase 4.5: Connection Monitor** — Live TCP/UDP socket tracking with process attribution and debounced search.
- **Comprehensive App Tests** — New `tests/test_app_real.py` using Textual's testing framework, achieving 46% coverage of `app.py`.
- **macOS Toolkit Tests** — New `tests/test_macos_toolkit.py` with mock-based validation of native tools (`scutil`, `sw_vers`).

### Changed
- **Memory Optimization** — Added `__slots__` to all core data classes (DNS, Port, Latency, Bandwidth) to reduce memory footprint.
- **Test Modernization** — Refactored Phase 3 & 4 tests to use modern pytest patterns (fixtures, parametrization).
- **Roadmap Update** — Marked Phase 4 TUI Widget Integration as 100% COMPLETE.
- **Python Migration** — Fully updated to Python 3.14.

### Fixed
- **CI/CD Coverage** — Fixed GitHub Actions `coverage combine` step failing due to hidden `.coverage.*` files being ignored by the `upload-artifact@v4` action, and added cross-platform path mapping to `.coveragerc` to successfully merge macOS, Linux, and Windows coverage data.
- **UI Responsiveness** — Added debounce timer to Connection Monitor search to prevent UI lag during rapid typing.
- **Test Robustness** — Improved socket and subprocess mocking in `tests/conftest.py`.

## [0.5.7] - 2026-04-06

### Added
- **Modernization Phase 1: Development Tooling** — Comprehensive modernization of development workflow and tooling.
  - **UV package manager integration** - 10-100x faster than pip, written in Rust with modern Python workflows
  - **Pre-commit hooks** - Automated quality checks with ruff, mypy, bandit, codespell, gitleaks, and commitlint
  - **Makefile** - 20+ common development commands for faster workflow (`make help` for list)
  - **Environment configuration** - `.env.example` template with comprehensive settings
  - **Improvement plan** - `IMPROVEMENT_PLAN.md` with 5-phase modernization roadmap
  - **Type safety improvements** - Fixed critical mypy type errors throughout codebase

### Changed
- **Updated README.md** - Added modernization notice and detailed UV installation instructions
- **Updated AGENTS.md** - Added uv commands and updated development workflow
- **Migrated to Python 3.14.3** - Updated project to use latest Python version
- **Fixed subprocess.Popen calls** - Updated `universal_newlines=True` → `text=True` for Python 3.14 compatibility
- **Enhanced package structure** - Added missing `__init__.py` files for proper namespace packages
- **Updated dependencies** - Installed type stubs for requests library and other development tools

### Fixed
- **Type annotations** - Fixed DNS record type annotations and Popen timeout parameter issues
- **Import issues** - Resolved mypy import errors with proper package structure
- **Development workflow** - Streamlined setup with `make setup` command

## [0.5.6] - 2026-03-13

### Added
- **Phase 4.6: LAN Bandwidth Tester Widget** — live network I/O throughput monitor that requires no external tools.
  - New `LanBandwidthWidget` in the **Utilities** tab (`u` → LAN Bandwidth).
  - Interface selector: measure a specific adapter (e.g. `en0`, `eth0`) or aggregate across **All Interfaces**.
  - Duration selector: 5 / 10 / 30 / 60-second sampling window.
  - `DataTable` streams live RX / TX Mbps per second with Rich colour-coding:
    - 🟢 **Green** ≥ 100 Mbps · 🟡 **Yellow** ≥ 10 Mbps · 🔴 **Red** < 10 Mbps
  - Auto-formatting: values ≥ 1 000 Mbps displayed as Gbps.
  - Summary panel after test completes: Avg RX / Avg TX / Peak RX / Peak TX.
  - **Stop** button cancels an in-flight test gracefully via `workers.cancel_all()`.
  - Runs entirely on a background thread (`@work(thread=True)`) — UI never blocks.
  - Uses `psutil.net_io_counters()` only — **zero external dependencies**.
  - Pure static helpers (`list_interfaces`, `get_io_counters`, `bytes_to_mbps`, `format_mbps`, `color_mbps`, `build_interface_options`, `run_bandwidth_test`) for clean unit testing.
  - 64 new tests (`tests/test_phase4_lan_bandwidth.py`) — all passing.

### Changed
- Wired `LanBandwidthWidget` into `UtilityTool` nav bar and `ContentSwitcher` in `app.py`.
- Exported `LanBandwidthWidget` from the `tui.widgets` package.

## [0.5.5] - 2026-03-13

### Added
- **Phase 4.5: Connection Monitor Widget** — live TCP/UDP socket monitor with process attribution.
  - New `ConnectionMonitorWidget` in the **Utilities** tab (`u` → Connection Monitor).
  - `DataTable` showing: Protocol, Local Address, Remote Address, Status (colour-coded), PID, Process Name.
  - Filter dropdown: All / ESTABLISHED / LISTEN / TCP only / UDP only.
  - Real-time search bar filtering by process name or local address (case-insensitive).
  - Auto-Refresh toggle (10-second interval) with clear ON/OFF button state.
  - Row click copies the remote address to clipboard.
  - Runs entirely on a background thread (`@work(thread=True)`) — UI never blocks.
  - Uses `psutil.net_connections` with a per-run PID→name cache to minimise `Process()` calls.
  - Graceful handling of `AccessDenied` and `NoSuchProcess` (common when running without elevated privileges).
  - Pure static helpers (`gather_connections`, `apply_filter`, `apply_process_filter`, `color_status`, `format_connection_count`) for clean unit testing.
  - 71 new tests (`tests/test_phase4_connection_monitor.py`) — all passing.

### Changed
- Wired `ConnectionMonitorWidget` into `UtilityTool` nav bar and `ContentSwitcher` in `app.py`.
- Exported `ConnectionMonitorWidget` from the `tui.widgets` package.

## [0.5.4] - 2026-03-11

### Added
- **Phase 4.4: Live Path Analyzer Widget** — MTR-style latency and path analysis directly in the TUI.
  - New `LatencyAnalyzerWidget` in the **Utilities** tab (`u` → Latency Analyzer).
  - Per-hop `DataTable` showing: Hop #, IP Address, Hostname, Avg RTT (colour-coded green/yellow/red), Packet Loss.
  - Aggregate ping statistics summary: Avg / Min / Max / Jitter / Loss % with colour coding.
  - Runs entirely on a background thread (`@work(thread=True)`) — UI never freezes.
  - Uses `mtr` if installed, falls back gracefully to `traceroute` / `tracert` via Phase 3 utilities.
  - Concurrency guard prevents duplicate in-flight traces.
  - 39 new tests (`tests/test_phase4_latency_widget.py`) — all passing.
  - Pure static helpers (`validate_host`, `format_rtt`, `color_rtt`) for clean unit testing.

### Changed
- Wired `LatencyAnalyzerWidget` into `UtilityTool` nav bar and `ContentSwitcher` in `app.py`.
- Exported `LatencyAnalyzerWidget` from the `tui.widgets` package.

[0.5.8]: https://github.com/knowoneactual/Network-Triage-Tool/compare/v0.5.7...v0.5.8
[0.5.7]: https://github.com/knowoneactual/Network-Triage-Tool/compare/v0.5.6...v0.5.7
[0.5.6]: https://github.com/knowoneactual/Network-Triage-Tool/compare/v0.5.5...v0.5.6
[0.5.5]: https://github.com/knowoneactual/Network-Triage-Tool/compare/v0.5.4...v0.5.5
[0.5.4]: https://github.com/knowoneactual/Network-Triage-Tool/compare/v0.5.3...v0.5.4
