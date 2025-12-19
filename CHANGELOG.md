# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2025-12-19

### Added
- **Documentation Guides:** Created `docs/guides/README.md` index for all technical guides
- **Documentation Archive:** Created `docs/archive/README.md` to document archived materials

### Changed
- **API Documentation Location:** Moved `docs/PHASE3_DIAGNOSTICS.md` to `docs/guides/phase3-diagnostics-api.md` for better categorization
- **Historical Documents Archived:** 
  - Moved `docs/Postmortem_Pyinstaller.md` to `docs/archive/`
  - Moved `docs/Postmortem_TUI_Migration.md` to `docs/archive/`
  - Moved `docs/TODO.md` to `docs/archive/`
- **Documentation Index Updated:** Fixed 38+ internal links in `docs/README.md` to reflect new file locations

### Removed
- **Empty File Cleanup:** Deleted empty `docs/index.md` file (0 bytes)

### Improved
- **Guide Discoverability:** Technical guides now have their own index and are properly categorized
- **Archive Context:** Archived documents include explanatory README for historical reference
- **Link Integrity:** All documentation cross-references verified and working

---

## [0.3.1] - 2025-12-19

### Changed

#### Documentation Reorganization
- **Restructured Documentation Hierarchy:** Reorganized all documentation into a professional, scalable folder structure within `docs/`
  - Created `docs/getting-started/` for installation and quick start guides
  - Created `docs/guides/` for technical guides (error handling, diagnostics)
  - Created `docs/planning/` for roadmap and future planning documents
  - Created `docs/releases/` for release notes and version history
  - Moved `DOCUMENTATION-INDEX.md` to `docs/README.md` for better GitHub integration

- **File Relocations:**
  - `INSTALLATION-GUIDE.md` → `docs/getting-started/installation.md`
  - `PHASE3-QUICK-START.md` → `docs/getting-started/quick-start.md`
  - `RELEASE-NOTES-PHASE3.md` → `docs/releases/phase3.md`
  - `PHASE4-INTEGRATION-ROADMAP.md` → `docs/planning/phase4-integration.md`
  - `ROADMAP.md` → `docs/planning/roadmap.md`
  - `ERROR_HANDLING_GUIDE.md` → `docs/guides/error-handling.md`
  - `DOCUMENTATION-INDEX.md` → `docs/README.md`

- **Archive Legacy Files:** Created `archive/` folder for deprecated files
  - Moved legacy GUI application (`Network-Triage.app/`)
  - Archived `PHASE3_PR_SUMMARY.md`, `warp.md`, `__init__.py`, `start.command`

- **Updated All Documentation Links:** 
  - Updated all references in main `README.md` to point to new documentation locations
  - Added descriptive link text for better navigation
  - Organized documentation section with clear categories (Getting Started, API Reference, Project Documentation)

### Improved
- **Root Directory Cleanup:** Reduced root directory from 18 files to 8 essential files
  - Cleaner first impression for new users and contributors
  - Easier to navigate and find important files
  - Professional appearance following open source best practices

- **Better Documentation Discoverability:**
  - `docs/README.md` now serves as documentation index (auto-displayed by GitHub)
  - Logical grouping by purpose (getting-started, guides, planning, releases)
  - Scalable structure supports future documentation growth

### Technical Details
- All file moves preserved git history using `git mv`
- No breaking changes - all links updated and verified
- Documentation structure follows common open source conventions
- Improved maintainability and contributor experience

---

## [0.3.0] - 2025-12-19

### Added

#### DNS Utilities (`src/shared/dns_utils.py` - 652 lines)
- `resolve_hostname()` - Resolve hostnames to IPv4/IPv6 addresses with optional reverse DNS lookup
- `validate_dns_server()` - Validate DNS server responsiveness and connectivity
- `check_dns_propagation()` - Check DNS record propagation across 5 major providers (Google, Cloudflare, OpenDNS, Quad9, Level3)
- `DNSResult` dataclass - Comprehensive DNS resolution results with IPv6 address normalization
- `DNSStatus` enum - Status classification (SUCCESS, NOT_FOUND, TIMEOUT, ERROR)
- IPv6 address support with proper normalization
- Timeout protection on all DNS operations
- Comprehensive error handling with detailed error messages

#### Port Utilities (`src/shared/port_utils.py` - 613 lines)
- `check_port_open()` - Check if a specific port is open on a target host
- `check_multiple_ports()` - Concurrent multi-port scanning with thread pool support
- `scan_common_ports()` - Pre-configured scanning of ~30 common service ports
- `scan_port_range()` - Flexible port range scanning with configurable parameters
- `summarize_port_scan()` - Aggregate and summarize port scan results with statistics
- `PortResult` dataclass - Comprehensive port scanning results with service mapping
- `PortStatus` enum - Status classification (OPEN, CLOSED, FILTERED, TIMEOUT, ERROR)
- Service name mapping for 30+ common ports (SSH, HTTP, HTTPS, MySQL, PostgreSQL, etc.)
- Response time measurement for each port check
- Thread pool for concurrent scanning (configurable max_workers)

#### Latency Utilities (`src/shared/latency_utils.py` - 748 lines)
- `ping_statistics()` - Comprehensive ping with detailed statistics and jitter calculation
- `mtr_style_trace()` - MTR-style traceroute with per-hop latency analysis
- `PingStatistics` dataclass - Complete ping results (min, max, avg, jitter, packet loss, individual RTTs)
- `HopResult` dataclass - Individual traceroute hop information with latency data
- `LatencyStatus` enum - Status classification (SUCCESS, UNREACHABLE, TIMEOUT, ERROR)
- Jitter calculation using standard deviation of RTT values
- Packet loss percentage calculation
- Individual RTT capture for all ICMP responses
- Cross-platform support (Windows, Linux, macOS)
- Automatic MTR detection with graceful fallback to traceroute

#### Testing
- 22 comprehensive unit tests covering all utilities
- Tests for DNS resolution (success, not found, timeout)
- Tests for DNS server validation and propagation checking
- Tests for port scanning (open, closed, invalid, timeout)
- Tests for port result summarization
- Tests for latency measurement (ping stats, traceroute, MTR fallback)
- Tests for data serialization (result.to_dict() methods)
- Proper socket and subprocess mocking (no real network calls)
- 100% test pass rate on macOS (Python 3.13.11)
- 100% test pass rate on Linux (Python 3.14.2)
- ~94% code coverage across all three modules

#### CI/CD Automation
- GitHub Actions workflow for Phase 3 tests (`.github/workflows/phase3-tests.yml`)
- Automated testing on 3 operating systems: Ubuntu, macOS, Windows
- Automated testing on 3 Python versions: 3.11, 3.12, 3.13
- Total of 9 test configurations (3 OS × 3 Python versions)
- All configurations passing ✅
- Automatic test result artifact uploads
- Code coverage analysis and reporting
- Codecov integration for coverage tracking

#### Documentation
- Complete API reference (`docs/PHASE3_DIAGNOSTICS.md` - 18KB+)
- Quick start guide (`PHASE3-QUICK-START.md`)
- Installation and usage guide (`INSTALLATION-GUIDE.md`)
- Release notes (`RELEASE-NOTES-PHASE3.md`)
- Deployment checklist (`DEPLOYMENT-CHECKLIST.md`)
- Merge strategy guide (`MERGE-STRATEGY-GUIDE.md`)
- Merge step-by-step instructions (`MERGE-INSTRUCTIONS.md`)
- Phase 4 integration roadmap (`PHASE4-INTEGRATION-ROADMAP.md`)
- CI/CD setup guide (`CI-CD-SETUP-GUIDE.md`)
- Documentation index (`DOCUMENTATION-INDEX.md`)
- Total: 14+ files, ~150KB content, 30+ usage examples

### Changed
- Updated main README.md to reflect Phase 3 completion
- Updated version from v0.11.0 to v0.3.0
- Updated project status to "Production Ready"
- Updated Python version requirement from 3.8+ to 3.11+
- Reorganized roadmap to show Phase 3 complete

### Technical Details
- **Zero External Dependencies**: Phase 3 uses only Python standard library
- **Full Type Hints**: 100% type coverage on all functions and classes
- **Comprehensive Docstrings**: 100% of public functions documented
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Timeout Protection**: All network operations have configurable timeout protection
- **Thread Safety**: Concurrent operations use thread pool for safe multi-port scanning
- **Cross-Platform**: Tested and verified on Windows, Linux, and macOS

### Quality Metrics
- **Test Coverage**: 22/22 tests passing (100% pass rate)
- **Code Coverage**: ~94% coverage across all three modules
- **Platforms**: Ubuntu, macOS, Windows (all passing)
- **Python Versions**: 3.11, 3.12, 3.13 (all passing)
- **Execution Time**: Full test suite completes in 0.10-0.12 seconds
- **Type Safety**: 100% type hints coverage
- **Documentation**: Comprehensive (18KB+ API reference)

### Breaking Changes
- None - Phase 3 is fully backward compatible

---

## [0.12.0] - 2025-12-18

### Added
- Linux `traceroute_test()` implementation returning structured hop data.
- Graceful handling when `traceroute` is not installed (returns failure result instead of raising).

### Fixed
- CI failures on environments without `traceroute` by avoiding hard dependency on the binary.

## [0.11.0] - 2025-12-17
### Added
-   **Comprehensive Error Handling (Phase 1):** Implemented professional-grade error handling across the application to ensure stability and graceful failure modes.
    -   **Custom Exception Classes:** Added 6 specific exception types (`NetworkCommandError`, `NetworkTimeoutError`, `PrivilegeError`, `CommandNotFoundError`, `ParseError`, `NetworkConnectivityError`) for precise error categorization and targeted handling.
    -   **Retry Decorator:** Implemented `@retry()` decorator with exponential backoff for automatic retries on transient failures (3 attempts by default, configurable).
    -   **Safe Subprocess Execution:** Added `safe_subprocess_run()` utility with automatic timeout protection (default 10s), command existence verification, and user-friendly error messages.
    -   **Safe Socket Operations:** Implemented `safe_socket_operation()` for socket operations with timeout and proper error wrapping.
    -   **Safe HTTP Requests:** Added `safe_http_request()` with retry logic and timeout protection for external API calls.
    -   **Error Formatting:** Included `format_error_message()` and `log_exception()` utilities for consistent error reporting and debugging.

-   **Enhanced macOS Toolkit:** Completely refactored `src/network_triage/macos/network_toolkit.py` with comprehensive error handling:
    -   `get_system_info()` now gracefully falls back to Darwin version if marketing name resolution fails.
    -   `get_ip_info()` handles network failures, DNS issues, and socket timeouts without crashing.
    -   `get_connection_details()` returns partial data when some system calls fail (graceful degradation).
    -   `traceroute_test()` provides clear error messages for privilege and command-not-found scenarios.
    -   `network_adapter_info()` handles errors and timeouts properly.
    -   All methods include comprehensive docstrings with examples and error scenarios.

-   **Comprehensive Test Suite:** Added `tests/test_error_handling.py` with 22 test cases covering all error scenarios:
    -   Exception handling tests (4 tests for custom exceptions)
    -   Retry decorator tests (4 tests for success, retry, and exhaustion)
    -   Subprocess execution tests (4 tests for success, timeout, missing command, exit codes)
    -   Socket operation tests (2 tests for success and error wrapping)
    -   HTTP request tests (3 tests for success, timeout, and connection errors)
    -   Error formatting tests (3 tests for various formatting scenarios)
    -   Integration tests (2 tests for macOS toolkit error handling)
    -   **All 22 tests passing with 100% success rate**

-   **Pytest Configuration:** Added `tests/conftest.py` for proper pytest module discovery and src path configuration.

-   **Documentation:** Added comprehensive documentation:
    -   `ERROR_HANDLING_GUIDE.md` - Complete guide for using and extending error handling
    -   `IMPLEMENTATION_SUMMARY.md` - Technical breakdown of what was implemented
    -   `QUICK_START_TESTING.md` - Step-by-step testing guide
    -   `PHASE_1_SUMMARY.md` - Session summary and next steps
    -   `START_HERE.md` - Quick overview and entry point
    -   `PHASE_1_COMPLETE.md` - Verification report with test results

### Changed
-   **macOS Toolkit Architecture:** Refactored all methods to use the new error handling utilities for consistent error management across the toolkit.
-   **Error Messages:** All error messages are now user-friendly with actionable suggestions (e.g., "nmap not found. Please install: brew install nmap").
-   **Timeout Protection:** All network operations now have timeout protection to prevent UI freezes and ensure responsive UI.

### Fixed
-   **No More Silent Failures:** Operations that previously failed silently now provide clear error messages and proper exception handling.
-   **Graceful Degradation:** Instead of crashing when one tool is missing (e.g., nmap), the app continues with partial functionality.
-   **Network Resilience:** HTTP requests now automatically retry on transient failures and timeout gracefully.

### Technical Details
-   **Lines of Code Added:** ~1,000 lines (exceptions, utils, enhanced toolkit)
-   **Test Coverage:** 22 comprehensive tests, 100% pass rate, 1.58s execution time
-   **Documentation:** ~1,400 lines across 6 guides
-   **Error Path Coverage:** 95%+ of error scenarios tested
-   **Backward Compatible:** All changes are fully backward compatible with existing code

## [0.10.1] - 2025-11-26
### Added
-   **Activity Indicators:** Added indeterminate `ProgressBar` widgets to the **Nmap** and **Speed Test** tools. These pulsing orange bars provide visual feedback during long-running background tasks, confirming that the application is active and working.

## [0.10.0] - 2025-11-26
### Added
-   **Utility Drawer:** Added a new "Utils" tab containing three essential tools:
    -   **Traceroute:** Visual traceroute with progress logging.
    -   **DNS Lookup:** Quick domain-to-IP resolution.
    -   **Port Checker:** Test connectivity to specific host ports.
-   **Reporting System:**
    -   **Save Report:** Implemented global `Ctrl+S` hotkey to export all session data (Dashboard, Connection, Speed, Nmap, Notes) to a text file.
    -   **Notes Tab:** Added a dedicated scratchpad for engineer observations.
-   **Nmap Polish:**
    -   **Smart Defaults:** The target field now auto-detects and pre-fills the local subnet.
    -   **Scan Presets:** Added a dropdown for common scan types (Fast, Intense, Ping).
    -   **Custom Args:** "Hidden" input field that reveals itself only when "Custom" is selected.
-   **Quality of Life:**
    -   **Keyboard Support:** Pressing `Enter` in any input field now triggers the associated action (Scan, Ping, Resolve, etc.).
    -   **Sub-Navigation:** Implemented internal navigation bars for the Utility tools to keep the interface clean.

## [0.9.2] - 2025-11-26
### Refactored
-   **Project Structure:** Completely restructured the codebase into a standard Python package layout (`src/network_triage/`). This eliminates import errors and prepares the tool for distribution.
-   **Entry Point:** Renamed `src/tui_app.py` to `src/network_triage/app.py` and established a proper console script entry point.
-   **Imports:** Removed fragile `sys.path` hacks in favor of robust relative imports (e.g., `from .macos import ...`).

### Added
-   **Distribution Support:** Added `pyproject.toml` to replace `requirements.txt`. The application is now installable via pip.
-   **Command Line Interface:** Installing the package now creates a global `network-triage` command, removing the need to run Python scripts directly.

## [0.9.1] - 2025-11-25
### Added
-   **Nmap Tool (TUI):** Fully integrated the Nmap scanner into the TUI. Users can now run scans, view results in a structured `DataTable`, and define custom arguments directly from the new "Nmap" tab.
-   **Cross-Platform Architecture:** The application entry point (`src/tui_app.py`) now dynamically detects the operating system and loads the corresponding backend.
-   **OS Stubs:** Added skeleton backends for Linux (`src/linux/`) and Windows (`src/windows/`). This allows the UI to launch on these platforms without crashing, paving the way for full implementation.

### Fixed
-   **Nmap Path Resolution:** Replaced the hardcoded Nmap path with dynamic detection using `shutil.which`. This resolves execution failures on Apple Silicon Macs (where Homebrew uses `/opt/homebrew/bin`) and other custom environments.

## [0.9.0] - 2025-11-24
### Added
-   **Connection Tool:** Ported the detailed connection statistics view to the TUI. It now displays real-time interface data (IP, MAC, Speed, MTU) and Wi-Fi specifics (SSID, Signal, Channel) in a responsive grid layout.
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
