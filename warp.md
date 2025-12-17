# Network Triage Tool - Warp Configuration

## Project Overview
A professional, cross-platform Terminal User Interface (TUI) for network diagnostics and troubleshooting. Built with Textual, this tool provides real-time network monitoring, Nmap scanning, speed tests, and various connectivity utilities - all from the terminal.

**Status:** Active development - transitioning from GUI to TUI architecture
**Branch:** switching-to-a-tui

## Tech Stack
- **Language:** Python 3.8+
- **UI Framework:** Textual (CSS-driven TUI)
- **Networking:** scapy, netmiko, python-nmap
- **System Info:** psutil, requests
- **Testing:** speedtest-cli for bandwidth measurements

## Project Structure
```
src/network_triage/
├── app.py                  # Main TUI application entry point
├── triage.tcss            # Textual CSS styling
├── shared/                # Cross-platform shared utilities
│   └── shared_toolkit.py
├── macos/                 # macOS-specific implementations
│   ├── main_app.py        # Legacy GUI (being phased out)
│   └── network_toolkit.py
├── linux/                 # Linux-specific implementations
└── windows/               # Windows-specific implementations
```

## Development Setup

### Initial Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dependencies
pip install -e .
```

### Running the Application
```bash
# Primary command (installed via pyproject.toml)
network-triage

# Some features may require elevated privileges
sudo network-triage
```

### Common Development Commands
```bash
# Run from source during development
python -m network_triage.app

# Check dependencies
pip list

# Reinstall after changes to pyproject.toml
pip install -e .

# View logs/debug output
# (Application runs in terminal - output is live)
```

## Key Features
- **Live Dashboard:** Real-time system info, IP addresses, gateway status
- **Nmap Scanner:** Fast/Intense presets, custom arguments, subnet auto-detection
- **Speed Test:** Non-blocking speedtest-cli integration
- **Continuous Ping:** Live scrolling ping results
- **Utilities:** Traceroute, DNS lookup, port checker
- **LLDP/CDP:** Packet capture for switch/port identification
- **Reporting:** Save full diagnostic reports (Ctrl+S)
- **Keyboard-first navigation:** Shortcuts for all actions

## Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `d` | Dashboard |
| `s` | Speed Test |
| `p` | Ping Tool |
| `c` | Connection Details |
| `q` | Quit |
| `Ctrl+S` | Save Report |

## Important Notes
- Raw packet capture (LLDP/CDP) requires `sudo` privileges
- Supports 256-color terminals (standard on macOS/Linux/Windows Terminal)
- SSH-compatible - runs entirely in terminal
- Legacy GUI code in `src/network_triage/macos/main_app.py` is being phased out

## Testing
```bash
# Run tests (if test suite exists)
pytest tests/

# Test specific features
network-triage  # Launch and test interactively
```

## Contributing
See CONTRIBUTING.md and ROADMAP.md for development guidelines and planned features.

## Troubleshooting
- **Command not found:** Ensure virtual environment is activated and `pip install -e .` was run
- **Permission errors:** Use `sudo` for packet capture features
- **Import errors:** Check all dependencies installed: `pip install -r requirements.txt`
- **Terminal rendering issues:** Ensure terminal supports 256 colors

## Related Files
- `CHANGELOG.md` - Version history and changes
- `ROADMAP.md` - Planned features and development direction
- `CONTRIBUTING.md` - Contribution guidelines
- `pyproject.toml` - Package configuration and dependencies
- `start.command` / `start-work.sh` - Launch scripts (legacy)
