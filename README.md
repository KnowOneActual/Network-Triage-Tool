### ⚠️ Current Status: Work in Progress ⚠️

I'm early stages of development and should be considered **unstable**. While the basic functions described below are operational, features may change, break, or be incomplete.


# Network Triage Tool

[![Status](https://img.shields.io/badge/status-active%20development-green)](https://github.com/knowoneactual/Network-Triage-Tool)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

A standalone GUI application designed to help network people quickly diagnose and troubleshoot common network issues.

![Screenshot of the Network Triage Tool](/img/readme_assets/Screenshot_midpoint_000001.webp)

## 🚧 Project Status

This project is currently undergoing a major refactor to support multiple operating systems. The initial cross-platform approach has been replaced with a more robust architecture that will have dedicated versions for each OS.

-   ✅ **macOS:** The macOS version is stable and functional.
-   ⏳ **Windows:** Coming soon.
-   ⏳ **Linux (Debian):** Coming soon.

## ✨ Features

The Network Triage Tool provides a tab-based interface to consolidate essential network diagnostic utilities into a single, easy-to-use application.

-   **Triage Dashboard:** Get an at-a-glance overview of your system (OS, hostname) and network connection (internal IP, gateway, public IP).
-   **Connection Details:** View detailed information about your active network interface, including IP address, MAC address, connection speed, and Wi-Fi details (SSID, signal strength, channel).
-   **Performance:** Run an internet speed test to measure your download speed, upload speed, and latency.
-   **Connectivity Tools:**
    -   **Continuous Ping:** Ping a host or IP address to check for reachability and packet loss.
    -   **Traceroute:** Trace the path that packets take to a destination host.
    -   **DNS Lookup:** Resolve a domain name to its corresponding IP address.
    -   **Port Scan:** Check if a specific port is open on a given host.
-   **Physical Layer Discovery:** Use LLDP and CDP packet sniffing to discover information about the directly connected switch, such as its name, management address, and port ID.
-   **Advanced Diagnostics:** Directly connect to network devices (routers, switches) via SSH to run commands and view the output.
-   **Save Report:** Export all collected data from all tabs into a single, easy-to-share text file.

## 🚀 Getting Started (macOS)

### Prerequisites
-   Python 3.7+

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/knowoneactual/Network-Triage-Tool.git](https://github.com/knowoneactual/Network-Triage-Tool.git)
    cd Network-Triage-Tool
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

Because the application requires administrator privileges for certain functions (like traceroute and packet sniffing), you must run it as a module from the root directory of the project.

```bash
python3 -m src.macos.main_app
The application will prompt you for your password to relaunch with the necessary permissions.

🤝 Contributing
Contributions are welcome! If you have a suggestion or find a bug, please open an issue to discuss it. If you'd like to contribute directly, you can also open a pull request.

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.