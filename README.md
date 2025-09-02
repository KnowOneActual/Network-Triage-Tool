# Network Triage Tool

[![Status](https://img.shields.io/badge/status-work%20in%20progress-yellow)](https://github.com/knowoneactual/Network-Triage-Tool)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

**Note**: This project is in the early stages of development. Features may be incomplete or subject to change. It is not yet recommended for production use.



A cross-platform network diagnostics and troubleshooting utility with a simple graphical user interface. Designed to be intuitive enough for end-users and helpdesk technicians, yet powerful enough for seasoned network engineers.

The goal of this project is to create a standalone, single-executable application that can be run on any user's machine to quickly gather diagnostic information, run connectivity tests, and generate a report that can be sent to an IT department for analysis.


## Features

The tool consolidates many common network troubleshooting tasks into a clean, tabbed interface.


### Triage Dashboard



* **System Information:** Gathers essential host details like OS, hostname, and IP addresses.
* **IP Information:** Displays internal IP, gateway, and the public IP address.
* **Adapter Details:** Provides the full output of ipconfig /all or ifconfig for in-depth analysis.


### Connectivity Tools



* **Ping:** A simple interface to run a standard ping test against any host.
* **Traceroute:** Perform a traceroute to any destination to identify the path and potential points of failure.
* **DNS Lookup:** Quickly resolve a domain name to its IP address.
* **Port Scan:** Check if a specific TCP port is open on a target host.


### Local Discovery



* **LLDP Scan:** Listens for Link Layer Discovery Protocol (LLDP) packets to identify the connected switch name and port, helping to pinpoint a user's physical location on the network. *Note: May require administrator privileges.*


### Advanced Diagnostics



* **Direct Device Connection:** A dedicated interface for network engineers to connect directly to network devices (like Cisco IOS routers) via SSH/Telnet.
* **Run Common Commands:** Execute a variety of show commands to check interface status, logs, CPU usage, and BGP sessions from a simple-to-use panel.


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.


### Prerequisites



* Python 3.6+
* Tkinter (usually included with Python)


### Installation



1. **Clone the repository:** 
git clone [https://github.com/your-username/Network-Triage-Tool.git](https://github.com/your-username/Network-Triage-Tool.git) 
cd Network-Triage-Tool 

2. **Install the required Python packages:** 
pip install -r requirements.txt 
 

### Running the Application

To launch the GUI, run the main_app.py script:

python main_app.py 



## Roadmap

The ultimate goal is to package this application into a single, standalone executable for Windows, macOS, and Linux using **PyInstaller**. This will allow the tool to be distributed easily and run without requiring users to install Python or any dependencies.



* [ ] Complete the UI for all planned features in main_app.py.
* [ *] Create a requirements.txt file.
* [ ] Add a feature to export all collected data into a single text file.
* [ ] Create PyInstaller build scripts.
* [ ] Test executables on all target platforms.


## Contributing

Contributions are welcome! Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests to me.


## License

This project is licensed under the MIT License - see the LICENSE file for details.
