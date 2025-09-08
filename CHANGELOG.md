# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- PyInstaller configuration for creating standalone executables.

## [0.2.0] 

### Added
- **Modern UI Theme:** Integrated the `ttkbootstrap` library to provide a modern, dark theme ("darkly") for the entire application.
- **Status Bar:** Added a persistent status bar at the bottom of the window for user feedback messages (e.g., "Ready", "Scan complete").
- **Tooltips:** Implemented tooltips for buttons on the Dashboard to improve usability and provide context.

### Changed
- **Project Structure:** Major refactoring to support future multi-platform versions (Windows, Linux). Code is now split into `src/shared` for common logic and `src/macos` for OS-specific implementations.
- **UI Layout:** Relocated the "Save Report" button to the new status bar to prevent it from being hidden and to make it globally accessible.

### Fixed
- **macOS Wi-Fi Details:** Resolved a major known issue by replacing the previous Wi-Fi detection method with a more reliable implementation using `system_profiler`.
- **macOS Self-Elevation:** Fixed the application crashing after the administrator password prompt. The self-elevation logic was rewritten to work correctly when running the app as a module.
- **Numerous GUI Bugs:** Corrected various layout, import, and scope (`NameError`) bugs to stabilize the application.

### Removed
- **Unused Dependencies:** Cleaned up `requirements.txt` by removing `pyobjc-framework-CoreWLAN` and `Pillow`, as they are no longer used in the macOS version.

## [0.1.0] 

This marks the first functional version of the Network Triage Tool, consolidating various scripts into a single GUI application.

### Added
- **Initial GUI Structure:** Created the main application window using `tkinter` with a multi-tab interface.
- **Triage Dashboard:**
  - Displays basic system information (OS, Hostname).
  - Fetches and displays network information (Internal IP, Gateway, Public IP).
  - Added a "User Notes" section for custom text input.
- **Connectivity Tools:**
  - Implemented a continuous ping tool with start and stop controls.
  - Added a traceroute utility.
  - Added a DNS lookup tool.
  - Added a single-port scanner.
- **Physical Layer Discovery:**
  - Implemented LLDP and CDP packet sniffing to identify connected switch details.
  - Extracts System Name, Switch ID, Management Address, and Port Description.
- **Advanced Diagnostics:**
  - Built a UI to connect to network devices (routers/switches) via SSH using `netmiko`.
  - Added functionality to send commands to a connected device and view the output.
- **Reporting:**
  - Created a "Save Report" feature to export all collected data from all tabs into a single `.txt` file.
- **Project Files:**
  - Established `requirements.txt` for dependency management.
  - Created `README.md`, `CONTRIBUTING.md`, and `LICENSE`.

### Fixed
- Resolved numerous UI threading bugs to ensure the application remains responsive during network operations.
- Implemented robust, low-level packet parsing for LLDP to handle non-standard packet formats discovered during testing.

### Known Issues
- **Wi-Fi Details (macOS):** This feature is currently not functional on all macOS versions. Extensive testing has revealed a profound system-level anomaly on some Mac configurations where the operating system's own command-line tools and native frameworks incorrectly report the Wi-Fi status, making a universally reliable implementation impossible at this time. The feature is preserved in a separate branch for future investigation.
- **Self-Elevation on macOS:** The feature to automatically request administrator privileges for the packaged application is currently unstable and can cause the app to hang or crash on launch. This feature is also under review for a more robust implementation.