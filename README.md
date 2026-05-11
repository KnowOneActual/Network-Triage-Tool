<p align="center">
<img src="img/assets/readme/Network-Triage-Tool_logo_v3.webp" alt="alt text" width="150">
</p>

[![Status](https://img.shields.io/badge/status-Active-green)](https://github.com/knowoneactual/Network-Triage-Tool)
[![Version](https://img.shields.io/badge/version-0.7.0-blue)](https://github.com/knowoneactual/Network-Triage-Tool/releases)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![UI Framework](https://img.shields.io/badge/UI-Textual-orange)](https://textual.textualize.io/)
[![Tests](https://img.shields.io/badge/tests-passing-success)](./tests/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)](https://github.com/knowoneactual/Network-Triage-Tool/actions)

A cross-platform **Terminal User Interface (TUI)** designed for network professionals to diagnose and troubleshoot connectivity issues efficiently.

Unlike traditional GUI networking tools, this application runs entirely in the terminal, making it lightweight, fast, and fully capable of running over SSH sessions. It provides comprehensive diagnostics for DNS, ports, latency, and system connectivity—all presented through a responsive and modern interface.

---

## ✨ Features

The application uses **Textual** to provide a modern, mouse-supportive terminal interface with non-blocking background workers ensuring the UI never freezes.

* **🖥️ Live Dashboard:** Real-time monitoring of System Info, Internal/Public IP, and Gateway status.
* **🔧 Core Utilities Drawer:**
  * **Traceroute & Ping:** Non-blocking ping and traceroute tools.
  * **DNS Resolver:** Resolve A, AAAA, PTR records with timing metrics.
  * **Port Scanner:** Concurrent TCP scanning with common service mapping.
* **📈 Advanced Diagnostics:**
  * **Live Path Analyzer:** MTR-style per-hop latency and packet loss tracking.
  * **Connection Monitor:** Live TCP/UDP socket tracking with process identification.
  * **LAN Bandwidth Tester:** Interface-specific or aggregate local throughput measurement.
  * **Scheduled Scans:** Setup background interval-based checks (e.g., continuous pinging) without leaving the interface.
* **🌐 Nmap Scanner:** Built-in scanner with preset modes (Fast, Intense), custom arguments, and auto-detection of local subnets.
* **🔍 LLDP/CDP Capture:** Packet capture tool to identify connected switches and ports.
* **📝 Reporting & Exporting:** Integrated "Notes" tab, report generation (`Ctrl+S`), and JSON/CSV data exporting.
* **🧩 Plugin Architecture:** Expand the tool's capabilities via a Python entry point-based plugin system.
* **⌨️ Keyboard First:** Fully navigable via shortcuts, with `Enter` key support for all actions.

## 🚀 Getting Started

### Prerequisites

* **Python 3.12+** (3.14 recommended)
* A terminal with 256-color support
* **uv** (Ultra-fast Python package manager) - [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)

### Installation

**Method 1: uv (Recommended)**
```bash
# Clone and install
git clone https://github.com/knowoneactual/Network-Triage-Tool.git
cd Network-Triage-Tool

uv sync --all-extras
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the app
network-triage
```

**Method 2: pipx**
For isolated environments using traditional tools:
```bash
pipx install git+https://github.com/knowoneactual/Network-Triage-Tool.git
```

**Method 3: Docker**
Run in an isolated container with all dependencies:
```bash
docker build -t network-triage .
docker run -it --rm --cap-add=NET_ADMIN --cap-add=NET_RAW --privileged network-triage
```

### ⌨️ Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| `d` | Switch to **Dashboard** |
| `c` | Switch to **Connection Details** |
| `s` | Switch to **Speed Test** |
| `p` | Switch to **Ping Tool** |
| `l` | Switch to **LLDP Scan** |
| `n` | Switch to **Nmap Scanner** |
| `o` | Switch to **Notes** |
| `u` | Switch to **Utilities Drawer** |
| `Ctrl+S` | **Save Report** |
| `q` | **Quit** Application |

## 🛠️ Tech Stack

* **UI Framework:** [Textual](https://github.com/Textualize/textual)
* **Package Manager:** [uv](https://github.com/astral-sh/uv)
* **Quality & Linting:** [Ruff](https://github.com/astral-sh/ruff), Mypy, Pre-commit
* **Networking & System:** `scapy`, `netmiko`, `python-nmap`, `requests`, `psutil`
* **Modern Python:** Dataclasses, Type Hints, Asyncio, Context Managers

## 🛡️ Code Quality & Security

The project adheres to high modern standards with automated tooling:
- **Testing:** Comprehensive test suite utilizing `pytest` with async support (targeting >60% coverage).
- **Type Safety:** 100% type hints across public APIs verified by strict `mypy`.
- **Formatting:** `ruff` is used for linting and formatting.
- **Security:** Scanned with `bandit`, `gitleaks`, and `pip-audit`.

## 📚 Documentation

* **[Installation Guide](docs/getting-started/installation.md)**
* **[Quick Start Guide](docs/getting-started/quick-start.md)**
* **[Phase 3 Diagnostics API](docs/guides/phase3-diagnostics-api.md)** - Raw diagnostic modules reference.
* **[Error Handling Guide](docs/guides/error-handling.md)**
* **[Changelog](CHANGELOG.md)** - Version history and completed phases.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

To report bugs or request features, please **[open an issue](https://github.com/knowoneactual/Network-Triage-Tool/issues)**.

## 📄 License

This project is licensed under the [MIT License](LICENSE). You are free to use, copy, modify, and distribute the software.
