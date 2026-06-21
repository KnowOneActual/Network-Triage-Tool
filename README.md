<p align="center">
<img src="img/assets/readme/Network-Triage-Tool_logo_v3.webp" alt="alt text" width="150">
</p>

[![Status](https://img.shields.io/badge/status-Active-green)](https://github.com/knowoneactual/Network-Triage-Tool)
[![Version](https://img.shields.io/badge/version-0.7.1-blue)](https://github.com/knowoneactual/Network-Triage-Tool/releases)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![UI Framework](https://img.shields.io/badge/UI-Textual-orange)](https://textual.textualize.io/)
[![Tests](https://img.shields.io/badge/tests-passing-success)](./tests/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)](https://github.com/knowoneactual/Network-Triage-Tool/actions)
[![slop: not found](https://img.shields.io/badge/slop-not%20found-brightgreen)](https://no-slop.club)

A terminal user interface (TUI) to diagnose and troubleshoot network connectivity. It runs entirely in the terminal, making it lightweight and SSH-compatible. Use it to check DNS, ports, latency, and system routing.

---

## Features

Built with [Textual](https://github.com/Textualize/textual), the interface uses background workers to prevent UI freezes.

* **Live Dashboard**: Monitor system info, IP addresses (internal and public), and gateway status.
* **Core Utilities**: Ping, traceroute, DNS resolver (A, AAAA, and PTR records), and a TCP port scanner.
* **Diagnostics**:
  * **Path Analyzer**: MTR-style latency and packet loss tracking per-hop.
  * **Connection Monitor**: Live TCP/UDP socket tracking with process IDs.
  * **LAN Bandwidth Tester**: Local throughput measurement.
  * **Scheduled Scans**: Interval-based background checks.
* **Nmap Integration**: Scanner with preset modes, custom arguments, and subnet auto-detection.
* **LLDP/CDP Capture**: Identify connected switch ports.
* **Reports**: Notes tab with `Ctrl+S` report generation, plus JSON/CSV data exporting.
* **Plugins**: Python entry point-based plugin system.
* **Keyboard Control**: Navigation via shortcuts, with `Enter` to confirm actions.

## Getting Started

### Prerequisites

* Python 3.12+ (3.14 recommended)
* Terminal with 256-color support
* [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

### Installation

**Using uv**
```bash
git clone https://github.com/knowoneactual/Network-Triage-Tool.git
cd Network-Triage-Tool
uv sync --all-extras
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
network-triage
```

**Using pipx**
```bash
pipx install git+https://github.com/knowoneactual/Network-Triage-Tool.git
```

**Using Docker**
```bash
docker build -t network-triage .
docker run -it --rm --cap-add=NET_ADMIN --cap-add=NET_RAW --privileged network-triage
```

### Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| `d` | Switch to Dashboard |
| `c` | Switch to Connection Details |
| `s` | Switch to Speed Test |
| `p` | Switch to Ping Tool |
| `l` | Switch to LLDP Scan |
| `n` | Switch to Nmap Scanner |
| `o` | Switch to Notes |
| `u` | Switch to Utilities Drawer |
| `Ctrl+S` | Save Report |
| `q` | Quit application |

## Tech Stack

* **UI Framework:** [Textual](https://github.com/Textualize/textual)
* **Package Manager:** [uv](https://github.com/astral-sh/uv)
* **Formatting & Types:** [Ruff](https://github.com/astral-sh/ruff) and Mypy
* **Networking & System:** `scapy`, `netmiko`, `python-nmap`, `requests`, `psutil`

## Quality & Security

* **Tests:** Checked using `pytest` (async support, aiming for >60% coverage).
* **Types:** Strict type hints verified by `mypy`.
* **Linting:** Formatted and linted with `ruff`.
* **Security:** Scanned with `bandit` and `gitleaks` for vulnerabilities and secrets, plus `pip-audit` for dependencies.

## Documentation

* [Installation Guide](docs/getting-started/installation.md)
* [Quick Start Guide](docs/getting-started/quick-start.md)
* [Phase 3 Diagnostics API](docs/guides/phase3-diagnostics-api.md)
* [Error Handling Guide](docs/guides/error-handling.md)
* [Changelog](CHANGELOG.md)

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Open an issue on [GitHub](https://github.com/knowoneactual/Network-Triage-Tool/issues) to report bugs or request features.

## License

MIT License. See [LICENSE](LICENSE) for details.
