<p align="center">
<img src="img/assets/readme/Network-Triage-Tool_logo_v3.webp" alt="alt text" width="150">
</p>

> ### Status: Stalled at (v0.4.0 - Phase 4.3). I am taking some time to reevaluate the project's direction in light of the helpful feedback I've received. I also want to extend my gratitude for your support with the Network Triage Tool (TUI). Thank you for your patience and encouragement! 


[![Status](https://img.shields.io/badge/status-development-yellow)](https://github.com/knowoneactual/Network-Triage-Tool)
[![Version](https://img.shields.io/badge/version-0.4.0--phase4.3-blue)](https://github.com/knowoneactual/Network-Triage-Tool/releases)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![UI Framework](https://img.shields.io/badge/UI-Textual-orange)](https://textual.textualize.io/)
[![Tests](https://img.shields.io/badge/tests-106%2F106%20passing-success)](./tests/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)](https://github.com/knowoneactual/Network-Triage-Tool/actions)

A cross-platform **Terminal User Interface (TUI)** designed for network professionals to diagnose and troubleshoot connectivity issues efficiently.

Unlike the previous GUI version, this tool runs entirely in the terminal, making it lighter, faster, and fully capable of running over SSH sessions. **Now with comprehensive advanced diagnostics for DNS, ports, and latency measurement, plus integrated TUI widgets.**

## 🎯 Phase 4: TUI Widget Integration (In Progress)

### ✅ Phase 4.3: Port Scanner Widget (Dec 20, 2025) - COMPLETE

**New Port Scanner Widget:**
- ✅ Complete Textual widget with full port scanning integration
- ✅ Target host input field with validation
- ✅ 4 scan mode selector (Common Services, Single Port, Multiple Ports, Port Range)
- ✅ Port input parsing with intelligent validation
- ✅ Configurable timeout (1-30 seconds)
- ✅ Results table with Port, Service, Status, and Time columns
- ✅ Color-coded status display (Green=OPEN, Red=CLOSED, Yellow=FILTERED)
- ✅ Service name mapping for 30+ common ports
- ✅ Real-time loading state and progress tracking
- ✅ Summary statistics (Total/Open/Closed/Filtered/Avg Response Time)
- ✅ Concurrent TCP scanning (10 workers, non-blocking)
- ✅ Comprehensive error handling with context-specific messages
- ✅ Full integration with Phase 3 port utilities
- ✅ **49 comprehensive tests (100% passing)**
- ✅ Complete documentation with real-world usage examples

**Phase 4.2 DNS Resolver Widget (Already Complete):**
- ✅ Hostname input validation
- ✅ Query type selector (A, AAAA, BOTH, PTR, ALL records)
- ✅ Optional DNS server input
- ✅ Results table with Type, Value, and Query Time
- ✅ Real-time loading and progress tracking
- ✅ Comprehensive error handling
- ✅ **21 comprehensive tests (100% passing)**

**Phase 4.1 Foundation (Already Complete):**
- ✅ BaseWidget with error handling, progress tracking, status management
- ✅ AsyncOperationMixin with caching capabilities
- ✅ 5 Reusable Components (ResultsWidget, InputWidget, etc.)
- ✅ **36 comprehensive tests (100% passing)**

**Total Phase 4 Status: 106/106 tests passing (100%) 🎉**

### 🚀 Phase 4.4+: Additional Widgets (Planned)
- [ ] Latency Analyzer widget (ping + traceroute)
- [ ] Results history and export
- [ ] v0.4.0 final release

## ✨ Features

The application uses **Textual** to provide a modern, mouse-supportive terminal interface that never freezes.

* **🖥️ Live Dashboard:** Real-time monitoring of System Info, Internal/Public IP, and Gateway status.
* **🌐 Nmap Scanner:** Built-in scanner with preset modes (Fast, Intense), custom argument support, and auto-detection of local subnets.
* **📝 Reporting:** Integrated "Notes" tab and a **Save Report** feature (`Ctrl+S`) that exports a full diagnostic report to a text file.
* **🛠️ Utility Drawer:** Handy toolbox containing **Traceroute**, **DNS Lookup**, and **Port Checker**.
* **🚀 Speed Test:** Integrated `speedtest-cli` running on a background worker to prevent UI lockups.
* **📡 Continuous Ping:** Non-blocking ping tool that scrolls results live.
* **🔍 LLDP/CDP:** Packet capture tool to identify connected switches and ports.
* **⌨️ Keyboard First:** Fully navigable via shortcuts, with `Enter` key support for all actions.
* **🛡️ Robust Error Handling:** Automatic retries, timeout protection, and graceful degradation on all network operations.
* **🔬 Advanced Diagnostics:** Comprehensive DNS, port scanning, and latency measurement utilities (Phase 3).
* **🎨 TUI Widgets:** Integrated widgets for DNS resolution (Phase 4.2) and port scanning (Phase 4.3) with Foundation-based architecture for rapid feature development.

## 🚀 Getting Started

### Prerequisites

* Python 3.11+
* A terminal with 256-color support (Standard on macOS/Linux/Windows Terminal)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/knowoneactual/Network-Triage-Tool.git
    cd Network-Triage-Tool
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install in Editable Mode:**
    This installs the dependencies and creates the `network-triage` command while allowing you to edit code live.
    ```bash
    pip install -e .
    ```

### Running the Tool

Simply type the command in your terminal:

```bash
network-triage
```

*Note: Some features (like raw packet capture) may require `sudo` privileges depending on your OS.*

### ⌨️ Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| `d` | Switch to **Dashboard** |
| `s` | Switch to **Speed Test** |
| `p` | Switch to **Ping Tool** |
| `c` | Switch to **Connection Details** |
| `n` | Switch to **Nmap Scanner** |
| `u` | Switch to **Utilities** |
| `q` | **Quit** Application |

## 🛠️ Tech Stack

  * **UI Framework:** [Textual](https://github.com/Textualize/textual) (CSS-driven TUI)
  * **Networking:** `scapy`, `netmiko`, `python-nmap`
  * **System Info:** `psutil`, `requests`
  * **Testing:** `pytest`, `pytest-mock` (106 comprehensive tests)
  * **Advanced Diagnostics:** Pure Python stdlib (Phase 3)

## 📊 Quality Metrics

| Metric | Value |
|--------|-------|
| **Test Coverage** | 106/106 tests passing (100%) |
| **Platform Support** | Ubuntu, macOS, Windows (CI/CD verified) |
| **Python Versions** | 3.11, 3.12, 3.13 (all tested) |
| **Code Quality** | 100% type hints, ~94% coverage |
| **Dependencies** | Zero external (Phase 3 uses stdlib only) |
| **Widget Tests** | Phase 4.1: 36, Phase 4.2: 21, Phase 4.3: 49 |
| **Execution Time** | 0.41s (Full test suite) |

## 📚 Phase 3 Usage

### DNS Resolution

```python
from src.shared.dns_utils import resolve_hostname

result = resolve_hostname('google.com')
print(f"IPv4: {result.ipv4_addresses}")
print(f"IPv6: {result.ipv6_addresses}")
```

### Port Scanning

```python
from src.shared.port_utils import check_multiple_ports

results = check_multiple_ports('localhost', [22, 80, 443])
for result in results:
    print(f"Port {result.port}: {result.status.value}")
```

### Latency Analysis

```python
from src.shared.latency_utils import ping_statistics

stats = ping_statistics('8.8.8.8', count=10)
print(f"Average latency: {stats.avg_ms:.2f}ms")
print(f"Jitter: {stats.stddev_ms:.2f}ms")
```

See [Quick Start Guide](docs/getting-started/quick-start.md) for more examples.

## 🔧 Advanced Diagnostics (Phase 3)

### What's Included

**DNS Utilities** (`src/shared/dns_utils.py`)
- Hostname to IP resolution (A/AAAA/PTR records)
- DNS server validation
- Multi-provider DNS propagation checking (5 providers)
- IPv6 address normalization
- Comprehensive timeout and error handling

**Port Utilities** (`src/shared/port_utils.py`)
- Single port connectivity testing
- Concurrent multi-port scanning with thread pool
- 30+ common service ports pre-configured
- Port status classification (OPEN/CLOSED/FILTERED)
- Result summarization with statistics

**Latency Utilities** (`src/shared/latency_utils.py`)
- Comprehensive ping statistics (min/max/avg/jitter)
- Packet loss percentage calculation
- MTR-style traceroute with per-hop latency
- Cross-platform support (Windows/Linux/macOS)
- Automatic tool detection and graceful fallback

## 🎨 Phase 4 TUI Widgets

### Phase 4.3: Port Scanner Widget (COMPLETE)

Integrated port scanning directly into the TUI with:
- Full host input validation
- 4 scan mode options (Common Services, Single, Multiple, Range)
- Intelligent port parsing and validation
- Concurrent TCP scanning (non-blocking)
- Color-coded results (Green/Red/Yellow status)
- Service name mapping for common ports
- Real-time loading and progress feedback
- Results displayed in structured table format
- Comprehensive error handling with context-specific messages
- Full Phase 3 port utilities integration

### Phase 4.2: DNS Resolver Widget (COMPLETE)

Integrated DNS resolution directly into the TUI with:
- Full hostname input validation
- Query type selection (A, AAAA, BOTH, PTR, ALL)
- Custom DNS server support
- Real-time loading and progress feedback
- Results displayed in structured table format
- Comprehensive error handling and user messages
- Full Phase 3 DNS utilities integration

### Architecture

Phase 4 widgets are built on a solid foundation:
- **BaseWidget:** Error handling, progress tracking, status management
- **AsyncOperationMixin:** Built-in caching and async operation support
- **Reusable Components:** ResultsWidget, InputWidget, StatusWidget for rapid development

This architecture eliminates code duplication and enables shipping new widgets in 1-2 hours.

## 📈 Roadmap

### ✅ Phase 1: macOS Stabilization (Complete)
- [x] Comprehensive error handling framework
- [x] Graceful degradation and timeout protection
- [x] 22 comprehensive tests (100% pass)

### ✅ Phase 2: TUI Framework (Complete)
- [x] Textual-based terminal interface
- [x] Dashboard and utilities tabs
- [x] Cross-platform design

### ✅ Phase 3: Advanced Diagnostics (Complete - v0.3.0)
- [x] DNS utilities (resolution, validation, propagation)
- [x] Port utilities (scanning, service mapping)
- [x] Latency utilities (ping, traceroute, jitter)
- [x] 22 comprehensive tests (100% passing)
- [x] CI/CD on 3 OS × 3 Python versions
- [x] Full API documentation (18KB+)
- [x] Zero external dependencies

### 🚀 Phase 4: TUI Widget Integration (In Progress - v0.4.0)

**Phase 4.1: Foundation** ✅ COMPLETE
- [x] BaseWidget with error handling, progress tracking
- [x] AsyncOperationMixin with caching
- [x] Reusable components (ResultsWidget, InputWidget, etc.)
- [x] 36 comprehensive tests

**Phase 4.2: DNS Resolver Widget** ✅ COMPLETE
- [x] Complete Textual widget implementation
- [x] Full Phase 3 DNS utilities integration
- [x] Hostname input validation
- [x] Query type selector (5 options)
- [x] Results table display
- [x] Error handling and status messages
- [x] 21 comprehensive tests
- [x] Production ready

**Phase 4.3: Port Scanner Widget** ✅ COMPLETE
- [x] Complete Textual widget implementation
- [x] Full Phase 3 port utilities integration
- [x] 4 scan mode options
- [x] Port input validation (1-65535)
- [x] Concurrent scanning (non-blocking)
- [x] Results table with service mapping
- [x] 49 comprehensive tests
- [x] Complete documentation and examples
- [x] Production ready

**Phase 4.4: Latency Analyzer Widget** (Planned - 1-2 weeks)
- [ ] Ping statistics display
- [ ] Traceroute with per-hop latency
- [ ] MTR-style analysis
- [ ] 20+ tests

**Phase 4.5: Results History & Export** (Planned - 2-3 weeks)
- [ ] Session result caching
- [ ] CSV/JSON export
- [ ] Comparison views
- [ ] Report generation

### 🎯 Phase 5+: Advanced Features (Future)
- [ ] Data visualization and charts
- [ ] Advanced analysis and trending
- [ ] Cloud integration
- [ ] Custom reporting

## 📚 Documentation

### Getting Started
- **[Installation Guide](docs/getting-started/installation.md)** - Setup instructions for all platforms
- **[Quick Start Guide](docs/getting-started/quick-start.md)** - Get started in 5 minutes

### API Reference
- **[Phase 3 Diagnostics API](docs/guides/phase3-diagnostics-api.md)** - Complete API reference (18KB+)

### Project Documentation
- **[Release Notes - Phase 3](docs/releases/phase3.md)** - What's new in v0.3.0
- **[Phase 4 Integration Roadmap](docs/planning/phase4-integration.md)** - Phase 4 planning and architecture
- **[Documentation Index](docs/README.md)** - Complete documentation map
- **[Error Handling Guide](docs/guides/error-handling.md)** - Error handling patterns
- **[CHANGELOG.md](CHANGELOG.md)** - Version history with all phases

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

To report bugs or request features, please **[open an issue](https://github.com/knowoneactual/Network-Triage-Tool/issues)**.

## 📄 License

This project is licensed under the MIT License. You are free to use, copy, modify, and distribute the software. See the [LICENSE](LICENSE) file for details.

---

## 🚧 Legacy Documentation

The previous GUI version is being phased out. Below is retained for reference only and will not be updated.

### Original Project: Network Triage Tool (GUI)

A standalone GUI application designed to help network professionals and enthusiasts quickly diagnose and troubleshoot common network issues from their desktop.

#### Features (GUI - Deprecated)

- Triage Dashboard with system overview
- Connection Details with interface information
- Performance monitoring and speed testing
- Connectivity Tools (Ping, Traceroute, DNS, Port Scan)
- Physical Layer Discovery (LLDP/CDP)
- Nmap Scanner integration
- Advanced Diagnostics with SSH support
- Report Export functionality

#### Platform Status (GUI - Deprecated)

- ✅ **macOS:** Legacy GUI stable but no longer maintained
- ❌ **Windows:** Not implemented
- ❌ **Linux:** Not implemented

For GUI-related information, see the legacy documentation in this repository's history.
