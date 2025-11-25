# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2025-11-24
### Added
-   **Manual Navigation Bar:** Implemented a custom, button-based navigation bar to replace the standard tab widget. This resolves rendering/overlap issues and ensures consistent visibility across different terminal emulators.
-   **Visual Polish:** Added emoji icons to navigation tabs (📊, 🔌, 🚀, 📡) and control buttons.
-   **Textual TUI:** Replaced the desktop GUI with a modern, cross-platform Terminal User Interface (TUI) using the Textual framework. The app now runs entirely in the terminal with full mouse and keyboard support.
-   **Async Workers:** Implemented non-blocking background workers (`@work` decorator) for **Continuous Ping** and **Speed Test**. This ensures the interface remains fully responsive and navigable while tests run.
-   **High-Contrast Theme:** Added a custom CSS theme (`src/triage.tcss`) featuring high-contrast colors ("Safety" palette) to ensure visibility across different terminal emulators.
-   **Keyboard Navigation:** Added global hotkeys (`d`, `s`, `p`, `c`, `q`) for rapid switching between tabs without requiring a mouse.

### Changed
-   **Speed Test Backend:** Updated the `speedtest-cli` integration to enforce HTTPS (`secure=True`). This resolves the `HTTP Error 403: Forbidden` issue caused by recent API changes.
-   **Application Entry:** The main entry point has moved from `src/macos/main_app.py` to `src/tui_app.py`.
-   **Tab Layout:** Replaced the `ttk.Notebook` widget with Textual's `TabbedContent` for a cleaner, CSS-styled navigation bar.
-   **Launcher:** Updated `start.command` to launch the new TUI application (`src/tui_app.py`) instead of the old GUI.

### Fixed
-   **UI Freezing:** Resolved the persistent "Not Responding" state during long-running tasks. You can now switch tabs and view the dashboard while a ping or speed test runs in the background.
-   **Cross-Platform Compatibility:** By moving to a TUI, the application no longer suffers from macOS-specific windowing/permission crashes associated with Tkinter.
-   **Layout Overlap:** Solved a critical CSS issue where the navigation bar would hide behind the header by implementing a simplified, flow-based layout structure.

### Removed
-   **Tkinter Dependencies:** Removed `ttkbootstrap` and all `tkinter` imports, significantly reducing the complexity of the build environment.

## [0.8.0] - 2025-10-11
### Added
-   **Nmap Host Details:** Implemented a "Click for Details" feature. Double-clicking a host in the scan results now opens a new window showing detailed OS, port, and service information.
-   **Nmap Custom Scans:** Added a "Custom" scan type that allows users to enter their own Nmap arguments for full control over the scanning process.
-   **Nmap Export to CSV:** Added an "Export CSV" button to save the results of a network scan to a CSV file.
-   **Nmap UI Feedback:** Added a progress bar and an instructional label to the Network Scan tab to improve user experience during scans.

### Changed
-   **Nmap Results Display:** Replaced the raw text output on the Network Scan tab with a structured, sortable table (Treeview) that displays IP Address, Hostname, Status, MAC Address, and Vendor. This provides a much cleaner and more readable overview of scan results.
-   **Nmap Backend:** Refactored the Nmap scanning logic to use a direct `subprocess` call that parses XML output. This approach is more reliable and robust than the previous library-based method.

### Fixed
-   Resolved a critical bug where Nmap scans would stall indefinitely due to a conflict with how the application handles administrator privileges.
-   Fixed an environment issue where the application could not find the Nmap executable when launched as a standalone app. The tool now uses a direct path to `nmap`.
-   Corrected the text alignment in the Nmap results table, ensuring both headers and data are properly left-aligned for readability.

## [0.7.0] - 2025-10-11
### Added
-   **Save Report:** Implemented a "Save Report" feature that gathers all diagnostic information from all tabs into a single, shareable text file.

### Changed
-   **macOS Launch Method:** The recommended way to run the application on macOS is now via a custom Automator application. This provides a true double-click experience without a terminal window appearing. The `README.md` has been updated with instructions.

### Fixed
-   Resolved a timing issue where the "Connection Details" section of a saved report could be empty if the report was saved before the details had finished loading on-screen.

## [0.6.0] - 2025-10-10
### Changed
-   **Distribution Method:** Replaced the `PyInstaller` build process with a more reliable Bash script launcher (`start.command`). This resolves numerous bundling and execution issues on macOS.
-   The application is now launched by double-clicking the `start.command` file, which handles the virtual environment and permissions automatically.

### Fixed
-   Corrected a persistent `ModuleNotFoundError` that occurred when launching the application as a script.
-   Restored the original, user-friendly graphical password prompt for administrator privileges, ensuring a seamless user experience.

## [0.5.0] - 2025-10-09
### Fixed
-   Resolved a major bug where the **Continuous Ping**, **DNS Lookup**, **Port Scan**, and **Physical Layer** scans would not work because their underlying functions were missing from the shared toolkit. All functions have been restored, and these features are now fully operational.

## [0.4.0] - 2025-10-09
### Added
-   Added a user-facing note on the **Connection** tab to explain that the SSID may show as `<redacted>` due to macOS privacy settings and should be manually recorded in the User Notes.

### Changed
-   The **Packet Loss** calculation on the Performance tab now correctly interprets a missing result from the speed test as **0.0%** instead of displaying "N/A".

### Fixed
-   Resolved a major issue where the speed test on the **Performance** tab would hang indefinitely during the upload phase.
-   Fixed a bug causing the progress bar on the **Performance** tab to remain incomplete after a speed test finished.
-   Corrected a typo in the backend (`mtU` instead of `mtu`) that caused all fields on the **Connection Details** tab to fail and display "N/A".
-   Stabilized the Wi-Fi detection logic to prevent crashes and correctly handle the `<redacted>` SSID value provided by newer macOS versions.
-   Restored the missing `run_speed_test` function to the shared toolkit, which was causing the Performance tab to crash.

## [0.3.0]
### Added
-   **Nmap Network Scan Tab:** Added a new tab dedicated to running Nmap scans.
-   **Scan Type Presets:** Implemented a dropdown menu with scan types (Ping, Fast, Intense) that use pre-configured Nmap arguments.
-   **Scan Progress Bar:** Added a progress bar that provides real-time feedback during Nmap scans.
-   **Scan Controls:** Added "Start Scan" and "Stop Scan" buttons for full control over the scanning process.
-   **Verbose Mode:** Included a toggle to show real-time, verbose output from the Nmap command.
-   **Gateway Pre-fill:** The target entry field is now automatically populated with the user's current network range (e.g., `192.168.1.0/24`).

### Changed
-   **Nmap Integration:** Refactored the backend to use Python's `subprocess` module for running Nmap. This provides more robust control and allows for real-time output and progress monitoring.
-   **UI Layout:** The controls on the Network Scan tab now use a two-row grid layout to ensure all widgets are visible and resize correctly.

### Fixed
-   Corrected a layout bug that was hiding the "Start Scan" and "Stop Scan" buttons on smaller window sizes.
-   Resolved an issue where the Nmap scan would appear to finish instantly by implementing a more reliable method for tracking scan progress.

## [0.2.0]

### Added
-   **Modern UI Theme:** Integrated the `ttkbootstrap` library to provide a modern, dark theme ("darkly") for the entire application.
-   **Status Bar:** Added a persistent status bar at the bottom of the window for user feedback messages (e.g., "Ready", "Scan complete").
-   **Tooltips:** Implemented tooltips for buttons on the Dashboard to improve usability and provide context.

### Changed
-   **Project Structure:** Major refactoring to support future multi-platform versions (Windows, Linux). Code is now split into `src/shared` for common logic and `src/macos` for OS-specific implementations.
-   **UI Layout:** Relocated the "Save Report" button to the new status bar to prevent it from being hidden and to make it globally accessible.
-   **macOS Name Resolution:** The OS version on the dashboard now displays the user-friendly macOS marketing name (e.g., "macOS Sonoma") instead of just the Darwin kernel version.

### Fixed
-   **macOS Wi-Fi Details:** Resolved a major known issue by replacing the previous Wi-Fi detection method with a more reliable implementation using `system_profiler`.
-   **macOS Self-Elevation:** Fixed the application crashing after the administrator password prompt. The self-elevation logic was rewritten to work correctly when running the app as a module.
-   **Numerous GUI Bugs:** Corrected various layout, import, and scope (`NameError`) bugs to stabilize the application.

### Removed
-   **Unused Dependencies:** Cleaned up `requirements.txt` by removing `pyobjc-framework-CoreWLAN` and `Pillow`, as they are no longer used in the macOS version.

## [0.1.0] - 2025-09-07

This marks the first functional version of the Network Triage Tool.