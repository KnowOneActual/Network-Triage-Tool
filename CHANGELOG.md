Changelog
All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog,
and this project adheres to Semantic Versioning.

[Unreleased]
Added
PyInstaller configuration for creating standalone executables.

[0.1.0]
This marks the first functional version of the Network Triage Tool, consolidating various scripts into a single GUI application.

Added
Initial GUI Structure: Created the main application window using tkinter with a multi-tab interface.

Triage Dashboard:

Displays basic system information (OS, Hostname).

Fetches and displays network information (Internal IP, Gateway, Public IP).

Added a "User Notes" section for custom text input.

Connectivity Tools:

Implemented a continuous ping tool with start and stop controls.

Added a traceroute utility.

Added a DNS lookup tool.

Added a single-port scanner.

Physical Layer Discovery:

Implemented LLDP and CDP packet sniffing to identify connected switch details.

Extracts System Name, Switch ID, Management Address, and Port Description.

Advanced Diagnostics:

Built a UI to connect to network devices (routers/switches) via SSH using netmiko.

Added functionality to send commands to a connected device and view the output.

Reporting:

Created a "Save Report" feature to export all collected data from all tabs into a single .txt file.

Project Files:

Established requirements.txt for dependency management.

Created README.md, CONTRIBUTING.md, and LICENSE.

Fixed
Resolved numerous UI threading bugs to ensure the application remains responsive during network operations.

Implemented robust, low-level packet parsing for LLDP to handle non-standard packet formats discovered during testing.

Removed
Wi-Fi Details (macOS): This feature is stalled, stored in a separate branch, and removed from the main application. 