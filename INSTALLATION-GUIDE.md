# Installation Guide

Complete installation and setup instructions for the Network Triage Tool.

## System Requirements

### Minimum Requirements
- **Python**: 3.11 or higher
- **Operating System**: Windows 10+, macOS 11+, Ubuntu 20.04+
- **Memory**: 512 MB RAM
- **Disk Space**: 100 MB

### Recommended Requirements
- **Python**: 3.12 or 3.13
- **Operating System**: Windows 11, macOS 14+, Ubuntu 22.04+
- **Memory**: 1 GB RAM
- **Terminal**: 256-color support (standard on modern terminals)

## Prerequisites

### Check Python Version

```bash
python3 --version
```

You should see:
```
Python 3.11.x or higher
```

If Python is not installed or version is too old:

**macOS:**
```bash
brew install python@3.13
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.13 python3.13-venv python3-pip
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/) and ensure "Add Python to PATH" is checked during installation.

### Optional Tools (Enhanced Features)

**Nmap** (for network scanning):
```bash
# macOS
brew install nmap

# Ubuntu/Debian
sudo apt install nmap

# Windows
# Download from https://nmap.org/download.html
```

**MTR** (for enhanced traceroute):
```bash
# macOS
brew install mtr

# Ubuntu/Debian
sudo apt install mtr

# Windows
# MTR not natively available, tool falls back to tracert
```

**speedtest-cli** (for speed testing):
```bash
pip install speedtest-cli
```

## Installation Methods

### Method 1: Standard Installation (Recommended)

This method installs the tool as a Python package with a global command.

#### Step 1: Clone Repository

```bash
git clone https://github.com/knowoneactual/Network-Triage-Tool.git
cd Network-Triage-Tool
```

#### Step 2: Create Virtual Environment

```bash
python3 -m venv .venv
```

#### Step 3: Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` prefix in your terminal prompt.

#### Step 4: Install Package

```bash
pip install -e .
```

The `-e` flag installs in "editable" mode, allowing you to modify the code while using the installed command.

#### Step 5: Verify Installation

```bash
network-triage --version
```

You should see:
```
Network Triage Tool v0.3.0
```

### Method 2: Direct Installation from Git

Install directly without cloning:

```bash
pip install git+https://github.com/knowoneactual/Network-Triage-Tool.git
```

### Method 3: Development Installation

For contributors and developers who want to modify the code:

```bash
# Clone with development branch
git clone https://github.com/knowoneactual/Network-Triage-Tool.git
cd Network-Triage-Tool
git checkout develop  # or feature branch

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"

# Install testing tools
pip install pytest pytest-cov pytest-mock
```

## Running the Tool

### TUI Application (Primary Interface)

After installation, launch the terminal user interface:

```bash
network-triage
```

**Note:** Some features (like packet capture for LLDP/CDP) may require elevated privileges:

```bash
sudo network-triage  # Linux/macOS
# Windows: Run terminal as Administrator
```

### Phase 3 Diagnostic Modules (Programmatic)

Use the diagnostic utilities directly in Python scripts:

```python
from src.shared.dns_utils import resolve_hostname
from src.shared.port_utils import scan_common_ports
from src.shared.latency_utils import ping_statistics

# Your diagnostic code here
```

See [PHASE3-QUICK-START.md](PHASE3-QUICK-START.md) for examples.

## Configuration

### Terminal Setup

For the best experience, ensure your terminal supports 256 colors:

**Check color support:**
```bash
echo $TERM
```

Should show `xterm-256color` or similar.

**If not, add to your shell profile:**
```bash
# ~/.bashrc or ~/.zshrc
export TERM=xterm-256color
```

### Recommended Terminals

- **macOS**: iTerm2, Terminal.app (built-in)
- **Windows**: Windows Terminal, WSL2 + any Linux terminal
- **Linux**: GNOME Terminal, Konsole, Alacritty, Kitty

### Font Recommendations

For emoji and icon support:
- JetBrains Mono
- Fira Code
- Source Code Pro
- Cascadia Code (Windows Terminal default)

## Platform-Specific Setup

### macOS Setup

#### Homebrew Installation (Recommended)

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and dependencies
brew install python@3.13 nmap mtr

# Clone and install Network Triage Tool
git clone https://github.com/knowoneactual/Network-Triage-Tool.git
cd Network-Triage-Tool
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

#### Permissions for Packet Capture

For LLDP/CDP features:
```bash
sudo network-triage
```

### Linux Setup (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python and tools
sudo apt install python3.13 python3.13-venv python3-pip git nmap mtr

# Clone and install
git clone https://github.com/knowoneactual/Network-Triage-Tool.git
cd Network-Triage-Tool
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

#### Grant Raw Socket Access (Optional)

To run without sudo for packet capture:
```bash
sudo setcap cap_net_raw+ep $(which python3)
```

### Windows Setup

#### Using Windows Terminal (Recommended)

1. Install Windows Terminal from Microsoft Store
2. Install Python 3.13 from [python.org](https://www.python.org/downloads/)
3. Install Nmap from [nmap.org](https://nmap.org/download.html)

```powershell
# Clone repository
git clone https://github.com/knowoneactual/Network-Triage-Tool.git
cd Network-Triage-Tool

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install
pip install -e .
```

#### Administrator Privileges

For packet capture and some network features, run as Administrator:
1. Right-click Windows Terminal
2. Select "Run as Administrator"
3. Navigate to project directory
4. Activate virtual environment and run tool

## Testing Installation

### Run Test Suite

```bash
# Activate virtual environment if not already active
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Run all tests
python -m pytest tests/ -v

# Run Phase 3 tests specifically
python -m pytest tests/test_phase3_diagnostics.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

**Expected output:**
```
======================== test session starts =========================
platform darwin -- Python 3.13.x, pytest-x.x.x
collected 22 items

tests/test_phase3_diagnostics.py::TestDNSUtils::test_resolve_hostname PASSED
tests/test_phase3_diagnostics.py::TestDNSUtils::test_validate_dns_server PASSED
...
======================== 22 passed in 0.10s ==========================
```

### Quick Functionality Check

```bash
# Test DNS resolution
python -c "from src.shared.dns_utils import resolve_hostname; print(resolve_hostname('google.com').ipv4_addresses)"

# Test port check
python -c "from src.shared.port_utils import check_port_open; print(check_port_open('8.8.8.8', 53))"

# Test ping
python -c "from src.shared.latency_utils import ping_statistics; print(ping_statistics('8.8.8.8', count=3).avg_ms)"
```

## Troubleshooting

### Common Issues

#### "Command not found: network-triage"

**Solution 1:** Ensure virtual environment is activated:
```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate  # Windows
```

**Solution 2:** Reinstall in editable mode:
```bash
pip install -e .
```

**Solution 3:** Run directly:
```bash
python -m src.network_triage.app
```

#### "ModuleNotFoundError: No module named 'textual'"

Install dependencies:
```bash
pip install -e .
```

Or manually:
```bash
pip install textual scapy netmiko python-nmap psutil requests
```

#### "Permission denied" on Linux/macOS

Run with sudo for packet capture features:
```bash
sudo network-triage
```

Or grant capabilities:
```bash
sudo setcap cap_net_raw+ep $(which python3)
```

#### Tests Failing on Windows

Some network tests may require Administrator privileges:
1. Open PowerShell or CMD as Administrator
2. Navigate to project directory
3. Activate virtual environment
4. Run tests

#### Slow DNS Resolution

Increase timeout values:
```python
from src.shared.dns_utils import resolve_hostname
result = resolve_hostname('example.com', timeout=10)  # Default is 5
```

#### Nmap Not Found

Ensure Nmap is installed and in PATH:

```bash
# Check if installed
which nmap  # macOS/Linux
where nmap  # Windows

# Install if missing (see Prerequisites section above)
```

## Uninstallation

### Remove Installation

```bash
# Deactivate virtual environment if active
deactivate

# Remove project directory
cd ..
rm -rf Network-Triage-Tool  # macOS/Linux
rmdir /s Network-Triage-Tool  # Windows
```

### Clean System-Wide Installation

If installed without virtual environment:
```bash
pip uninstall network-triage-tool
```

## Upgrading

### Update to Latest Version

```bash
cd Network-Triage-Tool
git pull origin main
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e . --upgrade
```

### Update Dependencies

```bash
pip install --upgrade -e .
```

## Next Steps

After installation:

1. **Launch the TUI**: `network-triage`
2. **Try Phase 3 utilities**: Read [PHASE3-QUICK-START.md](PHASE3-QUICK-START.md)
3. **Review documentation**: See [DOCUMENTATION-INDEX.md](DOCUMENTATION-INDEX.md)
4. **Run tests**: `pytest tests/ -v`
5. **Contribute**: Read [CONTRIBUTING.md](CONTRIBUTING.md)

## Getting Help

- **Documentation**: [DOCUMENTATION-INDEX.md](DOCUMENTATION-INDEX.md)
- **Issues**: https://github.com/knowoneactual/Network-Triage-Tool/issues
- **Discussions**: https://github.com/knowoneactual/Network-Triage-Tool/discussions

---

**Installation complete! Start with `network-triage` command. 🚀**
