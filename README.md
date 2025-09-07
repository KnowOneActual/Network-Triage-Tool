# Network Triage Tool

[![Status](https://img.shields.io/badge/status-work%20in%20progress-yellow)](https://github.com/knowoneactual/Network-Triage-Tool)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

### ⚠️ Current Status: Work in Progress ⚠️

This project is in the early stages of development and should be considered **unstable**. While the basic functions described below are operational, features may change, break, or be incomplete. Please use with this in mind and feel free to contribute or report bugs!


## Features

The Network Triage Tool provides a simple, tab-based interface to quickly gather critical network information.



* **Triage Dashboard:** Get at-a-glance information about the local machine, including OS, hostname, internal/public IP addresses, and default gateway.
* **Connectivity Tools:** A suite of essential tools for testing network reachability:
    * Continuous Ping
    * Traceroute
    * DNS Lookup
    * Port Scanning
* **Physical Layer Discovery:** Scan the local network for LLDP and CDP packets to identify the switch and port the machine is connected to.
* **Advanced Diagnostics:** Connect directly to network devices (routers, switches) via SSH to run commands and retrieve logs.
* **Save Report:** Export all gathered information from all tabs into a single, easy-to-share text file.


## Getting Started


### Prerequisites



* Python 3.6+
* pip for installing dependencies


### Installation



1. **Clone the repository:** 

```bash
git clone [https://github.com/knowoneactual/Network-Triage-Tool.git](https://github.com/knowoneactual/Network-Triage-Tool.git) 
cd Network-Triage-Tool 

```

2. **Create and activate a virtual environment:**
    * **macOS / Linux:** 

```bash
python3 -m venv .venv 
source .venv/bin/activate 

```

    * **Windows:** 

```bash
python -m venv .venv 
.\.venv\Scripts\activate 

```

3. **Install the required libraries:** 

```bash 
pip install -r requirements.txt 

```
 
*Note: On some systems, you may need to install libpcap or Npcap for the LLDP/CDP scanning feature to work.*


## Usage



1. Make sure your virtual environment is activated.
2. Run the main application file: 

```bash
python3 main_app.py 

```

3. On macOS and Linux, some features (like Traceroute and LLDP/CDP scanning) require administrator privileges to run correctly. You may need to run the application with sudo: 

```bash
sudo ./.venv/bin/python3 main_app.py 

```



## Contributing

Contributions are welcome! If you have a suggestion or find a bug, please open an issue to discuss it. If you'd like to contribute directly, you can also open a pull request.


## License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
