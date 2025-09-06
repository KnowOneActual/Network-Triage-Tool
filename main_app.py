import os
import platform
import queue
import re
import socket
import struct
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

import requests
import psutil
from netmiko import ConnectHandler
from scapy.all import sniff, inet_ntoa
from scapy.contrib.lldp import LLDPDU
from scapy.contrib.cdp import CDPMsg, CDPAddrRecord

from network_toolkit import NetworkTriageToolkit, RouterConnection

net_tool = NetworkTriageToolkit()


class TriageDashboard(ttk.Frame):
    """Dashboard for at-a-glance network info."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.info_labels = {}
        self.wifi_labels = {}
        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        """Create and arrange widgets on the dashboard."""
        info_frame = ttk.LabelFrame(self, text="System & Network Information")
        info_frame.pack(padx=10, pady=10, fill="x", expand=True)

        info_points = ["OS", "Hostname", "Internal IP", "Gateway", "Public IP"]
        for i, point in enumerate(info_points):
            label_title = ttk.Label(
                info_frame, text=f"{point}:", font=("Helvetica", 10, "bold")
            )
            label_title.grid(row=i, column=0, sticky="w", padx=5, pady=2)

            label_value = ttk.Label(info_frame, text="Loading...")
            label_value.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.info_labels[point] = label_value

        # --- New Wi-Fi Details Section ---
        wifi_frame = ttk.LabelFrame(self, text="Wi-Fi Details")
        wifi_frame.pack(padx=10, pady=10, fill="x", expand=True)

        wifi_points = ["SSID", "BSSID", "Signal", "Noise", "Channel"]
        for i, point in enumerate(wifi_points):
            label_title = ttk.Label(
                wifi_frame, text=f"{point}:", font=("Helvetica", 10, "bold")
            )
            label_title.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            label_value = ttk.Label(wifi_frame, text="Loading...")
            label_value.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.wifi_labels[point] = label_value

        # --- User Notes Section ---
        notes_frame = ttk.LabelFrame(self, text="User Notes")
        notes_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.notes_text = scrolledtext.ScrolledText(notes_frame, wrap=tk.WORD, height=5)
        self.notes_text.pack(padx=5, pady=5, fill="both", expand=True)

        # --- Buttons ---
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)
        refresh_button = ttk.Button(
            button_frame, text="Refresh Data", command=self.refresh_data
        )
        refresh_button.pack(side="left", padx=5)
        adapter_button = ttk.Button(
            button_frame, text="Show Full Adapter Info", command=self.show_adapter_info
        )
        adapter_button.pack(side="left", padx=5)

    def refresh_data(self):
        """Fetches and updates all data on the dashboard."""
        for label in self.info_labels.values():
            label.config(text="Loading...")
        for label in self.wifi_labels.values():
            label.config(text="Loading...")

        threading.Thread(target=self.task, daemon=True).start()

    def task(self):
        """The actual data-fetching task."""
        system_info = net_tool.get_system_info()
        ip_info = net_tool.get_ip_info()
        wifi_info = net_tool.get_wifi_details()

        all_info = {**system_info, **ip_info}

        # Update system and IP info
        for key, value in all_info.items():
            if key in self.info_labels:
                self.parent.after(0, self.info_labels[key].config, {"text": value})

        # Update Wi-Fi info
        for key, value in wifi_info.items():
            if key in self.wifi_labels:
                self.parent.after(0, self.wifi_labels[key].config, {"text": value})

    def show_adapter_info(self):
        """Displays full network adapter info in a new window."""
        info_window = tk.Toplevel(self.parent)
        info_window.title("Network Adapter Information")
        info_window.geometry("600x400")

        text_area = scrolledtext.ScrolledText(
            info_window, wrap=tk.WORD, width=70, height=20
        )
        text_area.pack(padx=10, pady=10, fill="both", expand=True)
        text_area.insert(tk.INSERT, "Fetching adapter information...")

        def fetch_and_display():
            adapter_info = net_tool.network_adapter_info()
            text_area.delete("1.0", tk.END)
            text_area.insert(tk.INSERT, adapter_info)

        threading.Thread(target=fetch_and_display, daemon=True).start()


class ConnectivityTools(ttk.Frame):
    """Tab for interactive tools like ping, traceroute, etc."""

    def __init__(self, parent):
        super().__init__(parent)
        self.create_ping_widgets()
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", padx=10, pady=5)
        self.create_other_tools_widgets()

    def create_ping_widgets(self):
        """Create the UI elements for the ping tool."""
        ping_frame = ttk.LabelFrame(self, text="Continuous Ping")
        ping_frame.pack(padx=10, pady=10, fill="x")

        control_frame = ttk.Frame(ping_frame)
        control_frame.pack(fill="x", padx=5, pady=5)

        host_label = ttk.Label(control_frame, text="Host/IP:")
        host_label.pack(side="left", padx=(0, 5))

        self.ping_host_entry = ttk.Entry(control_frame)
        self.ping_host_entry.pack(side="left", fill="x", expand=True)
        self.ping_host_entry.insert(0, "8.8.8.8")

        self.start_button = ttk.Button(
            control_frame, text="Start Ping", command=self.start_ping
        )
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(
            control_frame, text="Stop Ping", command=self.stop_ping, state="disabled"
        )
        self.stop_button.pack(side="left")

        self.ping_output_text = scrolledtext.ScrolledText(
            ping_frame, wrap=tk.WORD, height=10
        )
        self.ping_output_text.pack(padx=5, pady=5, fill="both", expand=True)

    def create_other_tools_widgets(self):
        """Create UI for Traceroute, DNS Lookup, and Port Scan."""
        tools_frame = ttk.Frame(self)
        tools_frame.pack(padx=10, pady=10, fill="x")

        trace_frame = ttk.LabelFrame(tools_frame, text="Traceroute")
        trace_frame.pack(fill="x", expand=True, pady=(0, 10))

        trace_host_label = ttk.Label(trace_frame, text="Host/IP:")
        trace_host_label.pack(side="left", padx=5, pady=5)
        self.trace_host_entry = ttk.Entry(trace_frame)
        self.trace_host_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.trace_host_entry.insert(0, "8.8.8.8")
        trace_button = ttk.Button(
            trace_frame, text="Run Trace", command=self.run_traceroute
        )
        trace_button.pack(side="left", padx=5, pady=5)

        dns_frame = ttk.LabelFrame(tools_frame, text="DNS Lookup")
        dns_frame.pack(fill="x", expand=True, pady=(0, 10))

        dns_host_label = ttk.Label(dns_frame, text="Domain:")
        dns_host_label.pack(side="left", padx=5, pady=5)
        self.dns_host_entry = ttk.Entry(dns_frame)
        self.dns_host_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.dns_host_entry.insert(0, "google.com")
        dns_button = ttk.Button(dns_frame, text="Lookup", command=self.run_dns_lookup)
        dns_button.pack(side="left", padx=5, pady=5)

        port_frame = ttk.LabelFrame(tools_frame, text="Port Scan")
        port_frame.pack(fill="x", expand=True)

        port_host_label = ttk.Label(port_frame, text="Host/IP:")
        port_host_label.pack(side="left", padx=5, pady=5)
        self.port_host_entry = ttk.Entry(port_frame)
        self.port_host_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.port_host_entry.insert(0, "google.com")

        port_label = ttk.Label(port_frame, text="Port:")
        port_label.pack(side="left", padx=5, pady=5)
        self.port_entry = ttk.Entry(port_frame, width=6)
        self.port_entry.pack(side="left", padx=5, pady=5)
        self.port_entry.insert(0, "443")
        port_button = ttk.Button(port_frame, text="Scan", command=self.run_port_scan)
        port_button.pack(side="left", padx=5, pady=5)

        output_frame = ttk.LabelFrame(self, text="Results")
        output_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.other_tools_output = scrolledtext.ScrolledText(
            output_frame, wrap=tk.WORD, height=10
        )
        self.other_tools_output.pack(padx=5, pady=5, fill="both", expand=True)

    def start_ping(self):
        """Starts the continuous ping thread."""
        host = self.ping_host_entry.get()
        if not host:
            messagebox.showerror("Error", "Please enter a host or IP address.")
            return

        self.ping_output_text.delete("1.0", tk.END)
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        def update_text(message):
            self.ping_output_text.insert(tk.END, message)
            self.ping_output_text.see(tk.END)

        self.ping_thread = threading.Thread(
            target=net_tool.continuous_ping, args=(host, update_text), daemon=True
        )
        self.ping_thread.start()

    def stop_ping(self):
        """Stops the continuous ping."""
        net_tool.stop_ping()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.ping_output_text.insert(tk.END, "\n--- Ping Stopped ---\n")

    def run_tool_in_thread(self, tool_function, *args):
        """Generic runner for single-shot tools to avoid freezing the GUI."""
        self.other_tools_output.delete("1.0", tk.END)
        self.other_tools_output.insert(
            tk.INSERT, f"Running {tool_function.__name__}..."
        )

        def task_wrapper():
            result = tool_function(*args)
            self.other_tools_output.delete("1.0", tk.END)
            self.other_tools_output.insert(tk.INSERT, result)

        threading.Thread(target=task_wrapper, daemon=True).start()

    def run_traceroute(self):
        host = self.trace_host_entry.get()
        if not host:
            messagebox.showerror("Error", "Please enter a host for the traceroute.")
            return
        self.run_tool_in_thread(net_tool.traceroute_test, host)

    def run_dns_lookup(self):
        domain = self.dns_host_entry.get()
        if not domain:
            messagebox.showerror("Error", "Please enter a domain to look up.")
            return
        self.run_tool_in_thread(net_tool.dns_resolution_test, domain)

    def run_port_scan(self):
        host = self.port_host_entry.get()
        port = self.port_entry.get()
        if not host or not port:
            messagebox.showerror(
                "Error", "Please enter both a host and a port to scan."
            )
            return
        self.run_tool_in_thread(net_tool.port_connectivity_test, host, port)


class AdvancedDiagnostics(ttk.Frame):
    """Tab for connecting to network devices and running commands."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.router_connection = None
        self.create_widgets()

    def create_widgets(self):
        conn_frame = ttk.LabelFrame(self, text="Device Connection")
        conn_frame.pack(padx=10, pady=10, fill="x")
        conn_frame.columnconfigure(1, weight=1)

        ttk.Label(conn_frame, text="Device IP:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.ip_entry = ttk.Entry(conn_frame)
        self.ip_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(conn_frame, text="Username:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.user_entry = ttk.Entry(conn_frame)
        self.user_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(conn_frame, text="Password:").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )
        self.pass_entry = ttk.Entry(conn_frame, show="*")
        self.pass_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(conn_frame, text="Device Type:").grid(
            row=3, column=0, sticky="w", padx=5, pady=2
        )
        self.device_type_combo = ttk.Combobox(
            conn_frame,
            values=[
                "cisco_ios",
                "cisco_xr",
                "cisco_nxos",
                "arista_eos",
                "juniper_junos",
            ],
        )
        self.device_type_combo.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        self.device_type_combo.set("cisco_ios")

        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=5)

        self.connect_button = ttk.Button(
            button_frame, text="Connect", command=self.connect_device
        )
        self.connect_button.pack(side="left", padx=5)
        self.disconnect_button = ttk.Button(
            button_frame,
            text="Disconnect",
            command=self.disconnect_device,
            state="disabled",
        )
        self.disconnect_button.pack(side="left", padx=5)

        self.status_label = ttk.Label(
            button_frame, text="Status: Disconnected", foreground="red"
        )
        self.status_label.pack(side="left", padx=10)

        cmd_frame = ttk.LabelFrame(self, text="Run Command")
        cmd_frame.pack(padx=10, pady=10, fill="x")
        cmd_frame.columnconfigure(0, weight=1)

        self.cmd_entry = ttk.Entry(cmd_frame)
        self.cmd_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.cmd_entry.insert(0, "show ip interface brief")
        self.send_cmd_button = ttk.Button(
            cmd_frame, text="Send Command", command=self.send_command, state="disabled"
        )
        self.send_cmd_button.grid(row=0, column=1, padx=5, pady=5)

        output_frame = ttk.LabelFrame(self, text="Device Output")
        output_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.output_text = scrolledtext.ScrolledText(
            output_frame, wrap=tk.WORD, height=15
        )
        self.output_text.pack(padx=5, pady=5, fill="both", expand=True)

    def connect_device(self):
        ip = self.ip_entry.get()
        user = self.user_entry.get()
        password = self.pass_entry.get()
        device_type = self.device_type_combo.get()

        if not all([ip, user, password, device_type]):
            messagebox.showerror("Error", "Please fill in all connection details.")
            return

        self.router_connection = RouterConnection(device_type, ip, user, password)
        self.status_label.config(text="Status: Connecting...", foreground="orange")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, f"Attempting to connect to {ip}...")

        threading.Thread(target=self.connection_task, daemon=True).start()

    def connection_task(self):
        result = self.router_connection.connect()

        def update_ui():
            self.output_text.insert(tk.END, f"\n{result}\n")
            if "successful" in result:
                self.status_label.config(text="Status: Connected", foreground="green")
                self.connect_button.config(state="disabled")
                self.disconnect_button.config(state="normal")
                self.send_cmd_button.config(state="normal")
            else:
                self.status_label.config(text="Status: Failed", foreground="red")
                self.router_connection = None

        self.parent.after(0, update_ui)

    def disconnect_device(self):
        if self.router_connection:
            result = self.router_connection.disconnect()
            self.output_text.insert(tk.END, f"\n{result}\n")

        self.status_label.config(text="Status: Disconnected", foreground="red")
        self.connect_button.config(state="normal")
        self.disconnect_button.config(state="disabled")
        self.send_cmd_button.config(state="disabled")
        self.router_connection = None

    def send_command(self):
        command = self.cmd_entry.get()
        if not command:
            messagebox.showerror("Error", "Please enter a command to send.")
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, f"Sending command: '{command}'...")

        threading.Thread(target=self.command_task, args=(command,), daemon=True).start()

    def command_task(self, command):
        if self.router_connection:
            result = self.router_connection.send_command(command)

            def update_ui():
                self.output_text.delete("1.d", tk.END)
                self.output_text.insert(tk.END, f"\n--- Output for '{command}' ---\n")
                self.output_text.insert(tk.END, result)

            self.parent.after(0, update_ui)


class LLDPDiscovery(ttk.Frame):
    """Tab for discovering connected switch and port via LLDP/CDP."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        """Create and arrange widgets for LLDP/CDP discovery."""
        lldp_frame = ttk.LabelFrame(self, text="LLDP / CDP Discovery")
        lldp_frame.pack(padx=10, pady=10, fill="both", expand=True)

        control_frame = ttk.Frame(lldp_frame)
        control_frame.pack(fill="x", padx=5, pady=5)

        self.start_button = ttk.Button(
            control_frame, text="Start Scan", command=self.start_scan
        )
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(
            control_frame, text="Stop Scan", command=self.stop_scan, state="disabled"
        )
        self.stop_button.pack(side="left")

        self.progress = ttk.Progressbar(
            lldp_frame, orient="horizontal", mode="indeterminate"
        )
        self.progress.pack(fill="x", padx=5, pady=(0, 5))

        self.output_text = scrolledtext.ScrolledText(
            lldp_frame, wrap=tk.WORD, height=15
        )
        self.output_text.pack(padx=5, pady=5, fill="both", expand=True)

    def start_scan(self):
        """Starts the LLDP/CDP packet capture."""
        self.output_text.delete("1.0", tk.END)
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress.start()

        def update_output(message):
            self.parent.after(0, self._update_text_widget, message)

        self.output_text.insert(
            tk.END, "Scanning for LLDP/CDP packets for 60 seconds...\n"
        )
        net_tool.start_discovery_capture(update_output)

    def _update_text_widget(self, message):
        """Helper method to safely update the text widget and UI state."""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)

        if any(
            keyword in message
            for keyword in ["Found", "Scan complete", "requires administrator", "Error"]
        ):
            self.progress.stop()
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

    def stop_scan(self):
        """Stops the LLDP/CDP packet capture."""
        net_tool.stop_discovery_capture()
        self.progress.stop()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.output_text.insert(tk.END, "\n--- Scan Stopped by User ---\n")


class MainApplication(tk.Tk):
    """The main application window."""

    def __init__(self):
        super().__init__()
        self.title("Network Triage Tool")
        self.geometry("600x800")  # Increased height for Wi-Fi info

        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=10, fill="both", expand=True)

        self.dashboard_tab = TriageDashboard(self)
        self.connectivity_tab = ConnectivityTools(self)
        self.lldp_tab = LLDPDiscovery(self)
        self.advanced_tab = AdvancedDiagnostics(self)

        notebook.add(self.dashboard_tab, text="Triage Dashboard")
        notebook.add(self.connectivity_tab, text="Connectivity Tools")
        notebook.add(self.lldp_tab, text="Physical Layer")
        notebook.add(self.advanced_tab, text="Advanced Diagnostics")

        report_button = ttk.Button(self, text="Save Report", command=self.save_report)
        report_button.pack(pady=10)

    def save_report(self):
        """Gathers data from all tabs and saves it to a text file."""
        report_content = []

        report_content.append("=" * 50)
        report_content.append("NETWORK TRIAGE REPORT")
        report_content.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_content.append("=" * 50 + "\n")

        report_content.append("--- System & Network Information ---")
        for key, label in self.dashboard_tab.info_labels.items():
            report_content.append(f"{key}: {label.cget('text')}")
        report_content.append("\n")

        report_content.append("--- Wi-Fi Details ---")
        for key, label in self.dashboard_tab.wifi_labels.items():
            report_content.append(f"{key}: {label.cget('text')}")
        report_content.append("\n")

        report_content.append("--- User Notes ---")
        report_content.append(self.dashboard_tab.notes_text.get("1.0", tk.END).strip())
        report_content.append("\n")

        report_content.append("--- Connectivity Tools Output ---")
        report_content.append("Ping Output:")
        report_content.append(
            self.connectivity_tab.ping_output_text.get("1.0", tk.END).strip()
        )
        report_content.append("\nOther Tools Output:")
        report_content.append(
            self.connectivity_tab.other_tools_output.get("1.0", tk.END).strip()
        )
        report_content.append("\n")

        report_content.append("--- Physical Layer (LLDP/CDP) Output ---")
        report_content.append(self.lldp_tab.output_text.get("1.0", tk.END).strip())
        report_content.append("\n")

        report_content.append("--- Advanced Diagnostics Output ---")
        report_content.append(self.advanced_tab.output_text.get("1.0", tk.END).strip())
        report_content.append("\n")

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Network Report",
            initialfile=f"network_report_{time.strftime('%Y%m%d_%H%M%S')}.txt",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(report_content))
                messagebox.showinfo(
                    "Success", f"Report saved successfully to:\n{file_path}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report: {e}")


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
