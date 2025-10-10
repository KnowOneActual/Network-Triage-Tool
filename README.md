### ⚠️ Current Status: Work in Progress ⚠️

This should be considered **unstable**. While the basic functions described below are operational, features may change, break, or be incomplete.


# Network Triage Tool

[![Status](https://img.shields.io/badge/status-active%20development-green)](https://github.com/knowoneactual/Network-Triage-Tool)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)


A standalone GUI application designed to help network professionals quickly diagnose and troubleshoot common network issues.


## 🚧 Project Status

This project is currently functional on macOS. The multi-platform refactor is ongoing.



* ✅ **macOS:** The macOS version is stable and launchable via the included script.
* ⏳ **Windows:** Coming soon.
* ⏳ **Linux (Debian):** Coming soon.


## ✨ Features

The Network Triage Tool offers a tab-based interface that consolidates essential network diagnostic utilities into a single, user-friendly application.



* **Triage Dashboard:** Get an at-a-glance overview of your system (OS, hostname) and network connection (internal IP, gateway, public IP).
* **Connection Details:** View detailed information about your active network interface, including IP address, MAC address, connection speed, and Wi-Fi details (SSID, signal strength, channel).
* **Performance:** Run an internet speed test to measure your download speed, upload speed, and latency.
* **Connectivity Tools:**
    * **Continuous Ping:** Ping a host or IP address to check for reachability and packet loss.
    * **Traceroute:** Trace the path that packets take to a destination host.
    * **DNS Lookup:** Resolve a domain name to its corresponding IP address.
    * **Port Scan:** Check if a specific port is open on a given host.
* **Physical Layer Discovery:** Use LLDP and CDP packet sniffing to discover information about the directly connected switch, such as its name, management address, and port ID.
* **Advanced Diagnostics:** Directly connect to network devices (routers, switches) via SSH to run commands and view the output.
* **Save Report:** Export all collected data from all tabs into a single, easy-to-share text file.


## 🚀 Getting Started (macOS)


### Prerequisites



* Python 3.7+


### Installation



1. **Clone the repository:** 

```bash
git clone [https://github.com/knowoneactual/Network-Triage-Tool.git](https://github.com/knowoneactual/Network-Triage-Tool.git) 
cd Network-Triage-Tool 
```

2. **Create a virtual environment:** 
```bash
python3 -m venv .venv 
source .venv/bin/activate 
```

3. **Install the required dependencies:** 
```bash
pip install -r requirements.txt 
```

4. Make the Launcher Executable (One-Time Step): 
You need to give the launcher script permission to run. Open your terminal in the project folder and run this command once: 
```bash
chmod +x start.command 
```



### Running the Application

To launch the application, simply **double-click the start.command file** in the project directory.

This will:



1. Open a new Terminal window.
2. Automatically activate the correct Python environment.
3. Launch the application, which will then show a graphical macOS prompt for your administrator password.

After you enter your password, the app will have the necessary permissions for all its features.

🤝 Contributing

Contributions are welcome! If you have a suggestion or find a bug, please open an issue to discuss it. If you'd like to contribute directly, you can also open a pull request.

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
