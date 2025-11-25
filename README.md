<p align="center">
<img src="img/assets/readme/Network-Triage-Tool_logo_v3.webp" alt="alt text" width="150">
</p>

### ⚠️ Current Status: Work in Progress ⚠️

# Following my testing, I have opted to pursue an alternative approach. I will discontinue the graphical user interface (GUI) in favor of the TUI. Since this represents a significant architectural transition, it will take time to implement properly. 

**This should be considered **unstable**. While the basic functions described below are operational, features may change, break, or be incomplete.**

# Network Triage Tool (TUI)

[![Status](https://img.shields.io/badge/status-active%20development-green)](https://github.com/knowoneactual/Network-Triage-Tool)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![UI Framework](https://img.shields.io/badge/UI-Textual-orange)](https://textual.textualize.io/)

A professional, cross-platform **Terminal User Interface (TUI)** designed for network professionals to diagnose and troubleshoot connectivity issues efficiently.

Unlike the previous GUI version, this tool runs entirely in the terminal, making it lighter, faster, and fully capable of running over SSH sessions.

## ✨ Features

The application uses **Textual** to provide a modern, mouse-supportive terminal interface that never freezes.

* **🖥️ Live Dashboard:** Real-time monitoring of System Info, Internal/Public IP, and Gateway status.
* **🚀 Speed Test:** Integrated `speedtest-cli` (with HTTPS/403 fix) running on a background worker to prevent UI lockups.
* **📡 Continuous Ping:** Non-blocking ping tool that scrolls results live while you navigate other tabs.
* **⌨️ Keyboard First:** Fully navigable via keyboard shortcuts for rapid triage.
* **🎨 High-Contrast Theme:** "Safety" color scheme designed for visibility in any terminal environment.

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* A terminal with 256-color support (Standard on macOS/Linux/Windows Terminal)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/knowoneactual/Network-Triage-Tool.git](https://github.com/knowoneactual/Network-Triage-Tool.git)
    cd Network-Triage-Tool
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Tool

Simply run the TUI app from your terminal.

```bash
python src/tui_app.py
````

*Note: Some features (like raw packet capture) may require `sudo` privileges depending on your OS.*

### ⌨️ Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| `d` | Switch to **Dashboard** |
| `s` | Switch to **Speed Test** |
| `p` | Switch to **Ping Tool** |
| `c` | Switch to **Connection Details** |
| `q` | **Quit** Application |

## 🛠️ Tech Stack

  * **UI Framework:** [Textual](https://github.com/Textualize/textual) (CSS-driven TUI)
  * **Networking:** `scapy`, `netmiko`, `python-nmap`
  * **System Info:** `psutil`, `requests`

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request for any bugs or feature additions.

## 📄 License

This project is licensed under the MIT License.


# Network Triage Tool (TUI)

[![Status](https://img.shields.io/badge/status-active%20development-green)](https://github.com/knowoneactual/Network-Triage-Tool)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![UI Framework](https://img.shields.io/badge/UI-Textual-orange)](https://textual.textualize.io/)

A professional, cross-platform **Terminal User Interface (TUI)** designed for network professionals to diagnose and troubleshoot connectivity issues efficiently.

Unlike the previous GUI version, this tool runs entirely in the terminal, making it lighter, faster, and fully capable of running over SSH sessions.

## ✨ Features

The application uses **Textual** to provide a modern, mouse-supportive terminal interface that never freezes.

* **🖥️ Live Dashboard:** Real-time monitoring of System Info, Internal/Public IP, and Gateway status.
* **🚀 Speed Test:** Integrated `speedtest-cli` (with HTTPS/403 fix) running on a background worker to prevent UI lockups.
* **📡 Continuous Ping:** Non-blocking ping tool that scrolls results live while you navigate other tabs.
* **⌨️ Keyboard First:** Fully navigable via keyboard shortcuts for rapid triage.
* **🎨 High-Contrast Theme:** "Safety" color scheme designed for visibility in any terminal environment.

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* A terminal with 256-color support (Standard on macOS/Linux/Windows Terminal)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/knowoneactual/Network-Triage-Tool.git](https://github.com/knowoneactual/Network-Triage-Tool.git)
    cd Network-Triage-Tool
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Tool

Simply run the TUI app from your terminal.

```bash
python src/tui_app.py
````

*Note: Some features (like raw packet capture) may require `sudo` privileges depending on your OS.*

### ⌨️ Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| `d` | Switch to **Dashboard** |
| `s` | Switch to **Speed Test** |
| `p` | Switch to **Ping Tool** |
| `c` | Switch to **Connection Details** |
| `q` | **Quit** Application |

## 🛠️ Tech Stack

  * **UI Framework:** [Textual](https://github.com/Textualize/textual) (CSS-driven TUI)
  * **Networking:** `scapy`, `netmiko`, `python-nmap`
  * **System Info:** `psutil`, `requests`

## 🤝 Contributing

Contributions are welcome\! Please open an issue or pull request for any bugs or feature additions.

## 📄 License

This project is licensed under the MIT [License](License).

# Old Project description. This Part of the project will not be updated!

# Network Triage Tool

# The old project descriptions are being systematically phased out.  
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
