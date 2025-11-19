<p align="center">
<img src="img/assets/readme/Network-Triage-Tool_logo_v2.webp" alt="alt text" width="150">
</p>

### ⚠️ Current Status: Work in Progress ⚠️

This should be considered **unstable**. While the basic functions described below are operational, features may change, break, or be incomplete.


# Network Triage Tool

[![Status](https://img.shields.io/badge/status-active%20development-green)](https://github.com/knowoneactual/Network-Triage-Tool)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)


A standalone GUI application designed to help network professionals and enthusiasts quickly diagnose and troubleshoot common network issues from their desktop.

## 🚧 Project Status

This project is currently fully functional on macOS.

  * ✅ **macOS:** Stable and ready for use.
  * ⏳ **Windows:** Coming soon.
  * ⏳ **Linux (Debian):** Coming soon.

## ✨ Features

The Network Triage Tool consolidates essential diagnostic utilities into a single, user-friendly, tab-based interface.

  * **Triage Dashboard:** Get an at-a-glance overview of your system (OS, hostname) and network connection (internal IP, gateway, public IP).
  * **Connection Details:** View detailed information about your active network interface, including IP address, MAC address, speed, and Wi-Fi details (SSID, signal strength, channel).
  * **Performance:** Run an internet speed test to measure your download speed, upload speed, and latency.
  * **Connectivity Tools:** Includes Continuous Ping, Traceroute, DNS Lookup, and Port Scan.
  * **Physical Layer Discovery:** Use LLDP and CDP packet sniffing to discover information about a directly connected switch.
  * **Nmap Scanner:** Run pre-configured or custom Nmap scans against your local network to discover hosts and services.
  * **Advanced Diagnostics:** Directly connect to network devices (routers, switches) via SSH to run commands.
  * **Save Report:** Export all collected data from all tabs into a single, easy-to-share text file.

## 🚀 Getting Started (macOS)

### Prerequisites

  * Python 3.7+

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/knowoneactual/Network-Triage-Tool.git
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

A simple, double-clickable application can be created using macOS's built-in Automator. This will launch the tool without a terminal window.

1.  **Open Automator** and create a new **Application**.
2.  Add the **Run AppleScript** action.
3.  Paste the following script into the window:
    ```applescript
    on run {input, parameters}
        -- Get the path to this Automator application
        set appPath to path to me
        
        -- Get the folder containing this application (which is the project root)
        tell application "Finder"
            set projectPath to POSIX path of (container of appPath as alias)
        end tell
        
        -- Construct the full command to run the Python module
        set pythonExecutable to quoted form of (projectPath & ".venv/bin/python3")
        set commandToRun to "cd " & quoted form of projectPath & " && " & pythonExecutable & " -m src.macos.main_app"
        
        -- Run the final command. The Python script's own code will trigger the graphical password prompt.
        do shell script commandToRun
    end run
    ```
4.  **Save** the application as "**Network Triage Tool**" inside the cloned project folder. 
5.  You can now **double-click** this new application to start the tool.

#### Alternative: Terminal Launch

You can still run the tool from the terminal if you prefer. First, make the included `start.command` script executable:

```bash
chmod +x start.command
```

Then, you can launch it by double-clicking `start.command` or running `./start.command` in your terminal.

## 🤝 Contributing

Contributions are welcome\! This project is open-source and lives on GitHub.

If you have a suggestion, find a bug, or want to add a new feature, please **[open an issue](https://www.google.com/search?q=https://github.com/knowoneactual/Network-Triage-Tool/issues)** to start a discussion. If you'd like to contribute directly, feel free to fork the repository and open a pull request.

## 📄 License

This project is licensed under the MIT License. You are free to use, copy, modify, and distribute the software. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
