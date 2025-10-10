# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### To-Do
-   Add icons to tabs and buttons.
-   Parse Nmap results into a user-friendly table.

## [0.5.0] - 2025-10-09
### Fixed
-   Resolved a major bug where the **Continuous Ping**, **DNS Lookup**, **Port Scan**, and **Physical Layer** scans would not work because their underlying functions were missing (Left out from troubleshooting <redacted>) from the shared toolkit. All functions have been restored, and these features are now fully operational.

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