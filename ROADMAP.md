### Phase 1: The Clean Slate (Setup)

We need to strip the weight before we build.

1.  **Dependency Swap**:
      * In `requirements.txt`:
          * Remove `ttkbootstrap`.
          * Add `textual`.
      * Run `pip install -r requirements.txt`.
2.  **Directory Check**:
      * Ensure `src/shared/` and `src/macos/` are accessible. We will reuse `network_toolkit.py` and `shared_toolkit.py` almost entirely (great job separating logic from UI earlier).

### Phase 2: The "Slick" Shell (UI Skeleton)

We will build the container that holds everything. This defines the look and feel immediately.

  * **Goal**: A running app with tabs, a header, and a footer, fully navigable by keyboard.
  * **Key Feature**: **Key Bindings**. Users should be able to press `d` for Dashboard, `p` for Ping, `q` to Quit.
  * **The "Slick" Factor**:
      * **Header**: Shows the time and tool name automatically.
      * **Footer**: Dynamically shows available keys based on the active tab.

### Phase 3: The Dashboard (Reactive Data)

The "Dashboard" tab is the perfect place to start because it is read-only.

  * **Goal**: Display OS, IP, and Gateway info.
  * **Tech**: Use Textual's **Reactive** attributes. Instead of manually refreshing labels, we update a variable `self.ip_address`, and the UI auto-updates.
  * **The "Slick" Factor**:
      * Auto-refresh every 60 seconds without blocking.
      * Use a grid layout so info aligns perfectly without pixel counting.

### Phase 4: The Workhorses (Async Workers)

This is the most critical technical phase. We port "Connectivity" (Ping) and "Performance" (Speedtest).

  * **Goal**: Run `continuous_ping` and `speedtest` without freezing the UI.
  * **Tech**: **Textual Workers**.
      * When the user clicks "Start Ping," we spawn a worker.
      * The worker pipes output to a `Log` widget (which auto-scrolls better than Tkinter's `ScrolledText`).
  * **The "Slick" Factor**:
      * **Multitasking**: The user can start a ping, switch to the Dashboard to check their IP, and switch back to see the ping still running.

### Phase 5: The Heavy Lifters (Nmap & Scapy)

Porting "Network Scan" and "Physical Layer" (LLDP).

  * **Goal**: Handle long-running processes that generate lots of text.
  * **Tech**:
      * **Nmap**: Use a `ProgressBar` widget.
      * **Scapy**: Since this requires `sudo`, we need to handle permission errors gracefully with a nice notification toast, not a crash.
      
      
### Phase 6: Visual Polish (CSS)

We stop coding Python and start coding `.tcss` (Textual CSS).

  * **Goal**: Make it look like a cohesive tool, not a default template.
  * **Tasks**:
      * Define a color palette (e.g., deeply saturated greens/blues for a "Network Ops" feel).
      * Style the `Log` widgets to look like CRT monitors (maybe a subtle border).
      * Create "Input" styles that clearly show focus.

### Phase 7: Distribution

Finally, we make it installable.

  * **Goal**: `pip install network-triage`.
  * **Tasks**:
      * Add a `pyproject.toml`.
      * Define a generic entry point so typing `network-triage` in the terminal launches the TUI.
