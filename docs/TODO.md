# Project Roadmap & To-Do List

This document tracks the remaining tasks to bring the Network Triage Tool (TUI) to feature parity with the original GUI and implement requested "Quality of Life" improvements.

**Current Focus:** macOS Feature Completion

## 🛑 Phase 1: Nmap & Scanning Polish (High Priority)
*Goal: Make the Nmap tool intuitive and fast to use without memorizing flags.*

- [ ] **Scan Presets (Dropdown):**
    - Replace the raw "Args" text input with a `Select` widget.
    - **Options:**
        - `Fast Scan (-F)` (Default)
        - `Intense Scan (-A -v)`
        - `Ping Scan (-sn)`
        - `Custom` (Reveals a text input for manual flags)
- [ ] **Auto-Fill Target:**
    - On app load, detect the user's current subnet/gateway (e.g., `192.168.1.0/24`) and pre-fill the Nmap target field.
    - *Dependency:* Requires exposing gateway logic from `src/macos/network_toolkit.py` to the main app.
- [ ] **Visual Tweaks:**
    - Style the Nmap `DataTable` headers to match the "Safety" color theme.

## 📝 Phase 2: Reporting & Documentation
*Goal: Allow the user to document findings and save a complete session report.*

- [ ] **User Notes Tab:**
    - Create a new tab with a large `TextArea` widget for typing observations.
    - Placeholder text: *"Enter notes here (e.g., 'Wall jack 3 is dead')..."*
- [ ] **Save Report Feature:**
    - Implement a "Save Report" action (Global `Ctrl+S` or Footer Button).
    - **Functionality:**
        - Gather data from: Dashboard, Connection Details, Speed Test, Nmap Results, and User Notes.
        - Write to a formatted text file (e.g., `Network_Triage_Report_YYYY-MM-DD.txt`) on the Desktop.
    - **Privacy:** Ensure redacted/sensitive info is handled correctly.

## 🛠️ Phase 3: The "Utility" Drawer
*Goal: Expose existing backend logic that currently has no UI.*

- [ ] **Utility Tab (New):**
    - Create a single tab to house smaller tools to avoid clutter.
- [ ] **Traceroute:**
    - UI: Input field (Host) + "Run" button + Output Log.
    - Backend: Hook up `traceroute_test` from `network_toolkit.py`.
- [ ] **DNS Lookup:**
    - UI: Input field (Domain) + "Resolve" button + Result Label.
    - Backend: Hook up `dns_resolution_test` from `shared_toolkit.py`.
- [ ] **Port Checker:**
    - UI: Input (Host) + Input (Port) + "Check" button.
    - Backend: Hook up `port_connectivity_test` from `shared_toolkit.py`.

## ✨ Phase 4: Quality of Life & Polish
*Goal: Make the tool feel professional and responsive.*

- [ ] **Clipboard Actions:**
    - Clicking an IP address (Dashboard/Connection) copies it to the clipboard.
- [ ] **Input History:**
    - Pressing `Up/Down` in IP input fields cycles through previously used addresses.
- [ ] **Error Handling (Toasts):**
    - Replace console logs with UI Toasts for common errors (e.g., "Sudo required", "Invalid IP").
- [ ] **Tab Badges:**
    - Add a visual indicator (dot/color change) to a tab if a background task (like a long scan) finishes while the user is on a different tab.

---
**Completed:**
- [x] Migrate to Textual TUI Framework
- [x] Implement Dashboard & System Info
- [x] Implement Speed Test & Continuous Ping (Async Workers)
- [x] Cross-Platform Entry Point (`src/tui_app.py`)
- [x] Basic Nmap Integration (DataTable results)