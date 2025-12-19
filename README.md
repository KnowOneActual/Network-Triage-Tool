<p align="center">
<img src="img/assets/readme/Network-Triage-Tool_logo_v3.webp" alt="alt text" width="150">
</p>

### ✅ Status: Production Ready (v0.3.0) - Phase 3 Complete

# Network Triage Tool (TUI)

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)](https://github.com/knowoneactual/Network-Triage-Tool)
[![Version](https://img.shields.io/badge/version-0.3.0-blue)](https://github.com/knowoneactual/Network-Triage-Tool/releases/tag/v0.3.0)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![UI Framework](https://img.shields.io/badge/UI-Textual-orange)](https://textual.textualize.io/)
[![Tests](https://img.shields.io/badge/tests-22%2F22%20passing-success)](./tests/test_phase3_diagnostics.py)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)](https://github.com/knowoneactual/Network-Triage-Tool/actions)

A cross-platform **Terminal User Interface (TUI)** designed for network professionals to diagnose and troubleshoot connectivity issues efficiently.

Unlike the previous GUI version, this tool runs entirely in the terminal, making it lighter, faster, and fully capable of running over SSH sessions. **Now with comprehensive advanced diagnostics for DNS, ports, and latency measurement.**

## 🎯 Phase 3: Advanced Diagnostics Complete ✅

**Release [v0.3.0](https://github.com/knowoneactual/Network-Triage-Tool/releases/tag/v0.3.0) (Dec 19, 2025) introduces comprehensive network diagnostics utilities:**

- ✅ **DNS Utilities:** Hostname resolution (A/AAAA/PTR), DNS server validation, multi-provider propagation checking
- ✅ **Port Utilities:** Single/concurrent port scanning, 30+ common service ports, result summarization
- ✅ **Latency Utilities:** Comprehensive ping with jitter, MTR-style traceroute with per-hop latency
- ✅ **Production Ready:** 22 tests (100% pass) on Windows, Linux, macOS with Python 3.11, 3.12, 3.13
- ✅ **Zero Dependencies:** Uses only Python standard library - no external packages required
- ✅ **Cross-Platform:** Tested and verified on Ubuntu, macOS, and Windows via CI/CD

### Phase 3 Highlights

| Component | Details |
|-----------|---------|
| **DNS Utilities** | `resolve_hostname()`, `validate_dns_server()`, `check_dns_propagation()` |
| **Port Utilities** | `check_port_open()`, `check_multiple_ports()`, `scan_common_ports()`, `summarize_port_scan()` |
| **Latency Utilities** | `ping_statistics()` with jitter, `mtr_style_trace()` with per-hop RTT |
| **Tests** | 22 comprehensive unit tests (100% passing on all platforms) |
| **CI/CD** | Automated testing on 3 OS × 3 Python versions = 9 configurations |
| **Code Quality** | 100% type hints, comprehensive error handling, ~94% coverage |
| **Documentation** | 18KB+ API reference + 14 guide documents |

See [RELEASE-NOTES-PHASE3.md](RELEASE-NOTES-PHASE3.md) for full details.

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
* **🔬 Advanced Diagnostics (NEW):** Comprehensive DNS, port scanning, and latency measurement utilities.

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

Simply type the command anywhere in your terminal:

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
  * **Testing:** `pytest`, `pytest-mock` (22 comprehensive tests)
  * **Advanced Diagnostics:** Pure Python stdlib (Phase 3)

## 📊 Quality Metrics

| Metric | Value |
|--------|-------|
| **Test Coverage** | 22/22 tests passing (100%) |
| **Platform Support** | Ubuntu, macOS, Windows (CI/CD verified) |
| **Python Versions** | 3.11, 3.12, 3.13 (all tested) |
| **Code Quality** | 100% type hints, ~94% coverage |
| **Dependencies** | Zero external (Phase 3 uses stdlib only) |
| **Execution Time** | 0.10s (Phase 3 tests) |

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

See [PHASE3-QUICK-START.md](PHASE3-QUICK-START.md) for more examples.

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

### 🚀 Phase 4: TUI Integration (Planned)
- [ ] DNS Resolver widget
- [ ] Port Scanner widget
- [ ] Latency Analyzer widget
- [ ] Results history and export
- [ ] v0.4.0 release

### 🎯 Phase 5+: Advanced Features (Future)
- [ ] Data visualization and charts
- [ ] Advanced analysis and trending
- [ ] Cloud integration
- [ ] Custom reporting

## 📚 Documentation

[quick-start.md](docs/getting-started/quick-start.md)
[installation.md](docs/getting-started/installation.md)
[phase3.md](docs/releases/phase3.md)
[phase4-integration.md](docs/planning/phase4-integration.md)
[README.md](docs/README.md)
[error-handling.md](docs/guides/error-handling.md)

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
