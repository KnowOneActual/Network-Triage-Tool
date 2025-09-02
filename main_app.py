# This is the main entry point for the Network Triage Tool GUI application.
# It uses Tkinter for the UI and calls the network_toolkit for all backend logic.

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

# Import the backend logic
import network_toolkit as net_tool


class NetworkTriageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Network Triage Tool")
        self.geometry("800x600")

        # Create the tab controller
        self.tabControl = ttk.Notebook(self)

        # Create tabs
        self.tab_triage = ttk.Frame(self.tabControl)
        self.tab_connectivity = ttk.Frame(self.tabControl)
        self.tab_discovery = ttk.Frame(self.tabControl)
        self.tab_advanced = ttk.Frame(self.tabControl)

        # Add tabs to the controller
        self.tabControl.add(self.tab_triage, text="Triage Dashboard")
        self.tabControl.add(self.tab_connectivity, text="Connectivity Tools")
        self.tabControl.add(self.tab_discovery, text="Local Discovery")
        self.tabControl.add(self.tab_advanced, text="Advanced Diagnostics")

        self.tabControl.pack(expand=1, fill="both")

        # Populate each tab
        self.create_triage_tab()
        self.create_connectivity_tab()
        self.create_discovery_tab()
        # self.create_advanced_tab() # Placeholder for future implementation

    def create_triage_tab(self):
        """Creates the content for the Triage Dashboard tab."""
        frame = self.tab_triage

        ttk.Label(frame, text="System Information", font=("Helvetica", 16)).pack(
            pady=10
        )

        self.info_labels = {}
        info_points = ["Hostname", "OS", "Internal IP", "Gateway", "External IP"]
        for point in info_points:
            row = ttk.Frame(frame)
            row.pack(fill="x", padx=20, pady=2)
            ttk.Label(row, text=f"{point}:", width=15, anchor="w").pack(side="left")
            self.info_labels[point] = ttk.Label(row, text="loading...", anchor="w")
            self.info_labels[point].pack(side="left")

        ttk.Button(frame, text="Refresh Info", command=self.refresh_triage_info).pack(
            pady=20
        )

        # Initial data load
        self.refresh_triage_info()

    def refresh_triage_info(self):
        """Callback to refresh the data on the triage tab."""

        def task():
            host_info = net_tool.get_host_info()
            ip_info = net_tool.get_ip_info()

            self.info_labels["Hostname"].config(text=host_info.get("hostname", "N/A"))
            self.info_labels["OS"].config(text=host_info.get("os", "N/A"))
            self.info_labels["Internal IP"].config(
                text=ip_info.get("internal_ip", "N/A")
            )
            self.info_labels["Gateway"].config(text=ip_info.get("gateway", "N/A"))
            self.info_labels["External IP"].config(
                text=ip_info.get("external_ip", "N/A")
            )

        # Run in a thread to not freeze the UI
        threading.Thread(target=task, daemon=True).start()

    def create_connectivity_tab(self):
        """Creates the content for the Connectivity Tools tab."""
        frame = self.tab_connectivity
        ttk.Label(frame, text="Continuous Ping", font=("Helvetica", 16)).pack(pady=10)

        # Input Frame
        input_frame = ttk.Frame(frame)
        input_frame.pack(pady=5)
        ttk.Label(input_frame, text="Target Host:").pack(side="left", padx=5)
        self.ping_host_entry = ttk.Entry(input_frame, width=20)
        self.ping_host_entry.pack(side="left")
        self.ping_host_entry.insert(0, "8.8.8.8")

        ttk.Button(input_frame, text="Start Ping", command=self.start_ping).pack(
            side="left", padx=5
        )
        # Add a Stop button later, which will need to manage the thread

        # Output Text Area
        self.ping_results_text = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, width=90, height=25
        )
        self.ping_results_text.pack(pady=10, padx=10, expand=True, fill="both")

    def start_ping(self):
        """Starts the continuous ping in a new thread."""
        host = self.ping_host_entry.get()
        if not host:
            return

        self.ping_results_text.delete("1.0", tk.END)
        self.ping_results_text.insert(tk.END, f"--- Starting ping to {host} ---\n")

        def update_text(line):
            self.ping_results_text.insert(tk.END, line + "\n")
            self.ping_results_text.see(tk.END)  # Auto-scroll

        # Run the ping tool in a thread so the UI doesn't freeze
        ping_thread = threading.Thread(
            target=net_tool.continuous_ping, args=(host, update_text), daemon=True
        )
        ping_thread.start()

    def create_discovery_tab(self):
        """Creates the content for the Local Discovery tab."""
        frame = self.tab_discovery
        ttk.Label(
            frame, text="Connected Switch Information (LLDP)", font=("Helvetica", 16)
        ).pack(pady=10)

        ttk.Button(
            frame, text="Scan for LLDP Information", command=self.start_lldp_scan
        ).pack(pady=10)

        self.lldp_result_text = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, width=90, height=15
        )
        self.lldp_result_text.pack(pady=10, padx=10)
        self.lldp_result_text.insert(
            tk.END,
            "Click the button to scan for LLDP packets for 15 seconds.\nNOTE: This may require administrator/sudo privileges to run.",
        )

    def start_lldp_scan(self):
        """Starts the LLDP scan in a separate thread."""
        self.lldp_result_text.delete("1.0", tk.END)
        self.lldp_result_text.insert(
            tk.END, "Scanning for LLDP packets... Please wait up to 15 seconds.\n"
        )

        def lldp_callback(data):
            self.lldp_result_text.delete("1.0", tk.END)
            if data.get("error"):
                self.lldp_result_text.insert(tk.END, f"Error: {data['error']}\n")
            else:
                self.lldp_result_text.insert(
                    tk.END, "--- LLDP Information Received ---\n"
                )
                self.lldp_result_text.insert(
                    tk.END, f"Switch Name: {data.get('switch_name', 'N/A')}\n"
                )
                self.lldp_result_text.insert(
                    tk.END, f"Switch Port: {data.get('port_id', 'N/A')}\n"
                )
                self.lldp_result_text.insert(
                    tk.END,
                    f"Switch Model/Description: {data.get('switch_model', 'N/A')}\n",
                )

        # Run in a thread to not freeze the UI
        threading.Thread(
            target=net_tool.run_lldp_scan, args=(lldp_callback,), daemon=True
        ).start()


if __name__ == "__main__":
    app = NetworkTriageApp()
    app.mainloop()
