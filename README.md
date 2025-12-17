<p align="center">
<img src="img/assets/readme/Network-Triage-Tool_logo_v3.webp" alt="alt text" width="150">
</p>

### ✅ Status: Stable (v0.11.0) - Phase 1 Complete

# Network Triage Tool (TUI)

[![Status](https://img.shields.io/badge/status-stable-brightgreen)](https://github.com/knowoneactual/Network-Triage-Tool)
[![Version](https://img.shields.io/badge/version-0.11.0-blue)](https://github.com/knowoneactual/Network-Triage-Tool/releases/tag/v0.11.0)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![UI Framework](https://img.shields.io/badge/UI-Textual-orange)](https://textual.textualize.io/)
[![Tests](https://img.shields.io/badge/tests-22%2F22%20passing-success)](./tests/test_error_handling.py)

A cross-platform **Terminal User Interface (TUI)** designed for network professionals to diagnose and troubleshoot connectivity issues efficiently.

Unlike the previous GUI version, this tool runs entirely in the terminal, making it lighter, faster, and fully capable of running over SSH sessions. **Now with comprehensive error handling and graceful failure modes for maximum stability.**

## 🎯 Phase 1: Stabilization Complete ✅

**Release [v0.11.0](https://github.com/knowoneactual/Network-Triage-Tool/releases/tag/v0.11.0) (Dec 17, 2025) introduces comprehensive error handling:**

- ✅ **Professional Error Handling:** 6 custom exception types, automatic retries, timeout protection
- ✅ **Graceful Degradation:** Missing tools no longer crash the app; operations timeout gracefully
- ✅ **Comprehensive Testing:** 22 unit tests (100% pass rate) covering all error scenarios
- ✅ **Enhanced macOS Toolkit:** All network operations wrapped with error handling
- ✅ **User-Friendly Errors:** Clear, actionable error messages with helpful suggestions

See [CHANGELOG.md](CHANGELOG.md#0110---2025-12-17) for full details.

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

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
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

## 📊 Quality Metrics

| Metric | Value |
|--------|-------|
| **Test Coverage** | 22/22 tests passing (100%) |
| **Error Scenarios** | 95%+ of error paths tested |
| **Execution Time** | 1.58s (full test suite) |
| **Platform Support** | macOS (stable), Linux/Windows (coming Phase 2) |
| **Code Documentation** | 100% method docstrings |

## 🔧 Error Handling (New in v0.11.0)

### What Happens When Things Go Wrong

**Before v0.11.0:**
```
❌ Missing tool (e.g., nmap) → App crashes
❌ Network timeout → UI freezes
❌ Permission denied → Unclear error
❌ API failure → Silent failure
```

**After v0.11.0 (Current):**
```
✅ Missing tool → "nmap not found. Install: brew install nmap"
✅ Network timeout → "Operation timed out. Please try again."
✅ Permission denied → "Requires administrator privileges. Run: sudo network-triage"
✅ API failure → "Failed to fetch IP info. Check your internet connection."
✅ All operations → Automatic retry with exponential backoff
```

### For Developers

See **[ERROR_HANDLING_GUIDE.md](./ERROR_HANDLING_GUIDE.md)** for:
- How to use error handling in your code
- Custom exception types and when to use each
- Retry decorator usage and configuration
- Testing error scenarios

## 📈 Roadmap

### ✅ Phase 1: macOS Stabilization (Complete)
- [x] Comprehensive error handling framework
- [x] Graceful degradation and timeout protection
- [x] 22 comprehensive tests (100% pass)
- [x] Professional documentation

### 🔄 Phase 2: Cross-Platform Support (In Progress)
- [ ] Linux toolkit with same error patterns
- [ ] Windows toolkit implementation
- [ ] Cross-platform testing
- [ ] v0.12.0 release

### 🚀 Phase 3: Polish & Release (Planned)
- [ ] Performance optimization
- [ ] Extended platform support
- [ ] Community feedback integration
- [ ] v1.0.0 release

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

To report bugs or request features, please **[open an issue](https://github.com/knowoneactual/Network-Triage-Tool/issues)**.

## 📚 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md)** - How to use and extend error handling
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical breakdown of v0.11.0 changes
- **[QUICK_START_TESTING.md](QUICK_START_TESTING.md)** - How to run the test suite
- **[START_HERE.md](START_HERE.md)** - Quick overview for new users

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
