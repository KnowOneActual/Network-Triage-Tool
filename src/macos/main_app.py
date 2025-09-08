import ttkbootstrap as tk
from ttkbootstrap import ttk
from tkinter import scrolledtext, messagebox, filedialog
from ttkbootstrap.tooltip import ToolTip
import webbrowser
import platform
import os
import sys
import subprocess
import time
import threading

# Relative import
from .network_toolkit import NetworkTriageToolkit, RouterConnection

net_tool = NetworkTriageToolkit()


class TriageDashboard(ttk.Frame):
    """Dashboard for at-a-glance network info."""

    def __init__(self, parent, main_app_instance):
        super().__init__(parent)
        self.parent = parent
        self.main_app = main_app_instance
        self.info_labels = {}
        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        """Create and arrange widgets on the dashboard."""
        info_frame = ttk.LabelFrame(self, text="System & Network Information")
        info_frame.pack(padx=10, pady=10, fill="x", expand=True)

        info_points = ["OS", "Hostname", "Internal IP", "Gateway", "Public IP"]
        for i, point in enumerate(info_points):
            label_title = ttk.Label(info_frame, text=f"{point}:")
            label_title.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            label_value = ttk.Label(info_frame, text="Loading...")
            label_value.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.info_labels[point] = label_value

        notes_frame = ttk.LabelFrame(self, text="User Notes")
        notes_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.notes_text = scrolledtext.ScrolledText(notes_frame, wrap=tk.WORD, height=5)
        self.notes_text.pack(padx=5, pady=5, fill="both", expand=True)
        self.notes_text.insert(tk.END, "Enter any relevant details about the issue here...")

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)
        refresh_button = ttk.Button(button_frame, text="Refresh Data", command=self.refresh_data)
        refresh_button.pack(side="left", padx=10)
        ToolTip(refresh_button, text="Refresh all system and network information.")
        adapter_button = ttk.Button(button_frame, text="Show Full Adapter Info", command=self.show_adapter_info)
        adapter_button.pack(side="left", padx=10)
        ToolTip(adapter_button, text="Display raw output from 'ifconfig'.")

    def refresh_data(self):
        """Fetches and updates the network info labels."""
        self.main_app.status_label.config(text="Refreshing data...")
        for label in self.info_labels.values():
            label.config(text="Loading...")
        threading.Thread(target=self.task, daemon=True).start()

    def task(self):
        """The actual data-fetching task."""
        system_info = net_tool.get_system_info()
        ip_info = net_tool.get_ip_info()
        all_info = {**system_info, **ip_info}
        def update_gui():
            for key, value in all_info.items():
                if key in self.info_labels:
                    self.info_labels[key].config(text=value)
            for label in self.info_labels.values():
                if label.cget("text") == "Loading...":
                    label.config(text="N/A")
            self.main_app.status_label.config(text="Ready")
        self.parent.after(0, update_gui)

    def show_adapter_info(self):
        """Displays full network adapter info in a new window."""
        info_window = tk.Toplevel(self.parent)
        info_window.title("Network Adapter Information")
        info_window.geometry("600x400")
        text_area = scrolledtext.ScrolledText(info_window, wrap=tk.WORD, width=70, height=20)
        text_area.pack(padx=10, pady=10, fill="both", expand=True)
        text_area.insert(tk.INSERT, "Fetching adapter information...")
        def fetch_and_display():
            adapter_info = net_tool.network_adapter_info()
            text_area.delete("1.0", tk.END)
            text_area.insert(tk.INSERT, adapter_info)
        threading.Thread(target=fetch_and_display, daemon=True).start()

class ConnectionDetails(ttk.Frame):
    def __init__(self, parent, main_app_instance):
        super().__init__(parent)
        self.parent = parent
        self.main_app = main_app_instance
        self.detail_labels = {}
        self.create_widgets()
        self.refresh_details()

    def create_widgets(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        note_label = ttk.Label(container, text="(Detailed info may take a moment to load)", font=("Helvetica", 9, "italic"))
        note_label.pack(side="top", pady=(0, 5), anchor="w", padx=5)
        connection_frame = ttk.LabelFrame(container, text="Connection Details")
        connection_frame.pack(fill="x", expand=True, side="top")
        self.wifi_frame = ttk.LabelFrame(container, text="Wi-Fi Details")
        self.detail_points = ["Connection Type", "Interface", "Status", "Speed", "MTU", "IP Address", "Netmask", "MAC Address", "DNS Servers"]
        self.wifi_points = ["SSID", "Signal", "Noise", "Channel"]
        for i, point in enumerate(self.detail_points):
            label_title = ttk.Label(connection_frame, text=f"{point}:")
            label_title.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            label_value = ttk.Label(connection_frame, text="Loading...")
            label_value.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.detail_labels[point] = label_value
        for i, point in enumerate(self.wifi_points):
            label_title = ttk.Label(self.wifi_frame, text=f"{point}:")
            label_title.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            label_value = ttk.Label(self.wifi_frame, text="Loading...")
            label_value.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.detail_labels[point] = label_value
        refresh_button = ttk.Button(self, text="Refresh Details", command=self.refresh_details)
        refresh_button.pack(pady=10)

    def refresh_details(self):
        self.main_app.status_label.config(text="Refreshing connection details...")
        for label in self.detail_labels.values():
            label.config(text="Loading...")
        self.wifi_frame.pack_forget()
        threading.Thread(target=self.task, daemon=True).start()

    def task(self):
        details = net_tool.get_connection_details()
        def update_ui():
            if details.get("Connection Type") == "Wi-Fi":
                self.wifi_frame.pack(fill="x", expand=True, side="top", pady=(10, 0))
            else:
                self.wifi_frame.pack_forget()
            all_points = self.detail_points + self.wifi_points
            for key in all_points:
                value = details.get(key, "N/A")
                if key in self.detail_labels:
                    self.detail_labels[key].config(text=value)
            self.main_app.status_label.config(text="Ready")
        self.parent.after(0, update_ui)

class PerformanceTab(ttk.Frame):
    def __init__(self, parent, main_app_instance):
        super().__init__(parent)
        self.parent = parent
        self.main_app = main_app_instance
        self.result_labels = {}
        self.create_widgets()

    def create_widgets(self):
        performance_frame = ttk.LabelFrame(self, text="Internet Speed Test")
        performance_frame.pack(padx=10, pady=10, fill="x")
        result_points = ["Ping", "Download", "Upload", "Packet Loss", "ISP", "Server"]
        for i, point in enumerate(result_points):
            label_title = ttk.Label(performance_frame, text=f"{point}:")
            label_title.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            label_value = ttk.Label(performance_frame, text="N/A")
            label_value.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.result_labels[point] = label_value
        label_title = ttk.Label(performance_frame, text="Result URL:")
        label_title.grid(row=len(result_points), column=0, sticky="w", padx=5, pady=2)
        self.style = ttk.Style()
        self.style.configure("Url.TLabel", foreground="#8be9fd")
        self.url_label = ttk.Label(performance_frame, text="N/A", style="Url.TLabel", cursor="hand2")
        self.url_label.grid(row=len(result_points), column=1, sticky="w", padx=5, pady=2)
        self.url_label.bind("<Button-1>", self.open_url)
        self.status_label = ttk.Label(performance_frame, text="Ready to start.")
        self.status_label.grid(row=len(result_points) + 1, columnspan=2, sticky="w", padx=5, pady=(10, 2))
        self.progress = ttk.Progressbar(performance_frame, orient="horizontal", mode="indeterminate")
        self.progress.grid(row=len(result_points) + 2, columnspan=2, sticky="ew", padx=5, pady=2)
        self.start_button = ttk.Button(self, text="Start Speed Test", command=self.start_test)
        self.start_button.pack(pady=10)

    def open_url(self, event):
        url = self.url_label.cget("text")
        if url.startswith("http"):
            webbrowser.open_new(url)

    def start_test(self):
        self.start_button.config(state="disabled")
        for label in self.result_labels.values():
            label.config(text="Testing...")
        self.url_label.config(text="Testing...")
        self.status_label.config(text="Finding the best server...")
        self.main_app.status_label.config(text="Running speed test...")
        self.progress.start(10)
        threading.Thread(target=self.run_test_task, daemon=True).start()

    def run_test_task(self):
        results = net_tool.run_speed_test()
        self.parent.after(0, self.update_ui, results)

    def update_ui(self, results):
        self.progress.stop()
        if "Error" in results:
            self.status_label.config(text=results["Error"])
            self.main_app.status_label.config(text="Speed test failed.")
            for label in self.result_labels.values():
                label.config(text="Failed")
            self.url_label.config(text="Failed")
        else:
            self.status_label.config(text="Test complete.")
            self.main_app.status_label.config(text="Speed test complete.")
            for key, value in results.items():
                if key in self.result_labels:
                    self.result_labels[key].config(text=value)
                elif key == "Result URL":
                    self.url_label.config(text=value)
        self.start_button.config(state="normal")

class ConnectivityTools(ttk.Frame):
    def __init__(self, parent, main_app_instance):
        super().__init__(parent)
        self.main_app = main_app_instance
        self.create_ping_widgets()
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=5)
        self.create_other_tools_widgets()

    def create_ping_widgets(self):
        ping_frame = ttk.LabelFrame(self, text="Continuous Ping")
        ping_frame.pack(padx=10, pady=10, fill="x")
        control_frame = ttk.Frame(ping_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(control_frame, text="Host/IP:").pack(side="left", padx=(0, 5))
        self.ping_host_entry = ttk.Entry(control_frame)
        self.ping_host_entry.pack(side="left", fill="x", expand=True)
        self.ping_host_entry.insert(0, "8.8.8.8")
        self.start_button = ttk.Button(control_frame, text="Start Ping", command=self.start_ping)
        self.start_button.pack(side="left", padx=5)
        self.stop_button = ttk.Button(control_frame, text="Stop Ping", command=self.stop_ping, state="disabled")
        self.stop_button.pack(side="left")
        self.ping_output_text = scrolledtext.ScrolledText(ping_frame, wrap=tk.WORD, height=10)
        self.ping_output_text.pack(padx=5, pady=5, fill="both", expand=True)

    def create_other_tools_widgets(self):
        tools_frame = ttk.Frame(self)
        tools_frame.pack(padx=10, pady=10, fill="x")
        trace_frame = ttk.LabelFrame(tools_frame, text="Traceroute")
        trace_frame.pack(fill="x", expand=True, pady=(0, 10))
        ttk.Label(trace_frame, text="Host/IP:").pack(side="left", padx=5, pady=5)
        self.trace_host_entry = ttk.Entry(trace_frame)
        self.trace_host_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.trace_host_entry.insert(0, "8.8.8.8")
        ttk.Button(trace_frame, text="Run Trace", command=self.run_traceroute).pack(side="left", padx=5, pady=5)
        dns_frame = ttk.LabelFrame(tools_frame, text="DNS Lookup")
        dns_frame.pack(fill="x", expand=True, pady=(0, 10))
        ttk.Label(dns_frame, text="Domain:").pack(side="left", padx=5, pady=5)
        self.dns_host_entry = ttk.Entry(dns_frame)
        self.dns_host_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.dns_host_entry.insert(0, "google.com")
        ttk.Button(dns_frame, text="Lookup", command=self.run_dns_lookup).pack(side="left", padx=5, pady=5)
        port_frame = ttk.LabelFrame(tools_frame, text="Port Scan")
        port_frame.pack(fill="x", expand=True)
        ttk.Label(port_frame, text="Host/IP:").pack(side="left", padx=5, pady=5)
        self.port_host_entry = ttk.Entry(port_frame)
        self.port_host_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.port_host_entry.insert(0, "google.com")
        ttk.Label(port_frame, text="Port:").pack(side="left", padx=5, pady=5)
        self.port_entry = ttk.Entry(port_frame, width=6)
        self.port_entry.pack(side="left", padx=5, pady=5)
        self.port_entry.insert(0, "443")
        ttk.Button(port_frame, text="Scan", command=self.run_port_scan).pack(side="left", padx=5, pady=5)
        output_frame = ttk.LabelFrame(self, text="Results")
        output_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.other_tools_output = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=10)
        self.other_tools_output.pack(padx=5, pady=5, fill="both", expand=True)

    def start_ping(self):
        host = self.ping_host_entry.get()
        if not host:
            messagebox.showerror("Error", "Please enter a host or IP address.")
            return
        self.ping_output_text.delete("1.0", tk.END)
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.main_app.status_label.config(text=f"Pinging {host}...")
        def update_text(message):
            self.ping_output_text.insert(tk.END, message)
            self.ping_output_text.see(tk.END)
        self.ping_thread = threading.Thread(target=net_tool.continuous_ping, args=(host, update_text), daemon=True)
        self.ping_thread.start()

    def stop_ping(self):
        net_tool.stop_ping()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.ping_output_text.insert(tk.END, "\n--- Ping Stopped ---\n")
        self.main_app.status_label.config(text="Ping stopped.")

    def run_tool_in_thread(self, tool_function, *args):
        self.other_tools_output.delete("1.0", tk.END)
        self.other_tools_output.insert(tk.INSERT, "Running...")
        self.main_app.status_label.config(text=f"Running {tool_function.__name__}...")
        def task_wrapper():
            result = tool_function(*args)
            self.other_tools_output.delete("1.0", tk.END)
            self.other_tools_output.insert(tk.INSERT, result)
            self.main_app.status_label.config(text="Scan complete.")
        threading.Thread(target=task_wrapper, daemon=True).start()

    def run_traceroute(self):
        host = self.trace_host_entry.get()
        if host: self.run_tool_in_thread(net_tool.traceroute_test, host)
        else: messagebox.showerror("Error", "Please enter a host for the traceroute.")

    def run_dns_lookup(self):
        domain = self.dns_host_entry.get()
        if domain: self.run_tool_in_thread(net_tool.dns_resolution_test, domain)
        else: messagebox.showerror("Error", "Please enter a domain to look up.")

    def run_port_scan(self):
        host = self.port_host_entry.get()
        port = self.port_entry.get()
        if host and port: self.run_tool_in_thread(net_tool.port_connectivity_test, host, port)
        else: messagebox.showerror("Error", "Please enter both a host and port.")

class AdvancedDiagnostics(ttk.Frame):
    def __init__(self, parent, main_app_instance):
        super().__init__(parent)
        self.parent = parent
        self.main_app = main_app_instance
        self.router_connection = None
        self.create_widgets()

    def create_widgets(self):
        conn_frame = ttk.LabelFrame(self, text="Device Connection")
        conn_frame.pack(padx=10, pady=10, fill="x")
        conn_frame.columnconfigure(1, weight=1)
        ttk.Label(conn_frame, text="Device IP:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.ip_entry = ttk.Entry(conn_frame)
        self.ip_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(conn_frame, text="Username:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.user_entry = ttk.Entry(conn_frame)
        self.user_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(conn_frame, text="Password:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.pass_entry = ttk.Entry(conn_frame, show="*")
        self.pass_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(conn_frame, text="Device Type:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.device_type_combo = ttk.Combobox(conn_frame, values=["cisco_ios", "cisco_xr", "cisco_nxos", "arista_eos", "juniper_junos"])
        self.device_type_combo.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        self.device_type_combo.set("cisco_ios")
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=5)
        self.connect_button = ttk.Button(button_frame, text="Connect", command=self.connect_device)
        self.connect_button.pack(side="left", padx=5)
        self.disconnect_button = ttk.Button(button_frame, text="Disconnect", command=self.disconnect_device, state="disabled")
        self.disconnect_button.pack(side="left", padx=5)
        self.status_label = ttk.Label(button_frame, text="Status: Disconnected", foreground="red")
        self.status_label.pack(side="left", padx=10)
        cmd_frame = ttk.LabelFrame(self, text="Run Command")
        cmd_frame.pack(padx=10, pady=10, fill="x")
        cmd_frame.columnconfigure(0, weight=1)
        self.cmd_entry = ttk.Entry(cmd_frame)
        self.cmd_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.cmd_entry.insert(0, "show ip interface brief")
        self.send_cmd_button = ttk.Button(cmd_frame, text="Send Command", command=self.send_command, state="disabled")
        self.send_cmd_button.grid(row=0, column=1, padx=5, pady=5)
        output_frame = ttk.LabelFrame(self, text="Device Output")
        output_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=15)
        self.output_text.pack(padx=5, pady=5, fill="both", expand=True)

    def connect_device(self):
        ip, user, password, device_type = (self.ip_entry.get(), self.user_entry.get(), self.pass_entry.get(), self.device_type_combo.get())
        if not all([ip, user, password, device_type]):
            messagebox.showerror("Error", "Please fill in all connection details.")
            return
        self.router_connection = RouterConnection(device_type, ip, user, password)
        self.status_label.config(text="Status: Connecting...", foreground="orange")
        self.main_app.status_label.config(text=f"Connecting to {ip}...")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, f"Attempting to connect to {ip}...")
        threading.Thread(target=self.connection_task, daemon=True).start()

    def connection_task(self):
        result = self.router_connection.connect()
        def update_ui():
            self.output_text.insert(tk.END, f"\n{result}\n")
            if "successful" in result:
                self.status_label.config(text="Status: Connected", foreground="green")
                self.main_app.status_label.config(text="Connected.")
                self.connect_button.config(state="disabled")
                self.disconnect_button.config(state="normal")
                self.send_cmd_button.config(state="normal")
            else:
                self.status_label.config(text="Status: Failed", foreground="red")
                self.main_app.status_label.config(text="Connection failed.")
                self.router_connection = None
        self.parent.after(0, update_ui)

    def disconnect_device(self):
        if self.router_connection:
            self.output_text.insert(tk.END, f"\n{self.router_connection.disconnect()}\n")
        self.status_label.config(text="Status: Disconnected", foreground="red")
        self.main_app.status_label.config(text="Disconnected.")
        self.connect_button.config(state="normal")
        self.disconnect_button.config(state="disabled")
        self.send_cmd_button.config(state="disabled")
        self.router_connection = None

    def send_command(self):
        command = self.cmd_entry.get()
        if not command:
            messagebox.showerror("Error", "Please enter a command.")
            return
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, f"Sending command: '{command}'...")
        self.main_app.status_label.config(text="Sending command...")
        threading.Thread(target=self.command_task, args=(command,), daemon=True).start()

    def command_task(self, command):
        if self.router_connection:
            result = self.router_connection.send_command(command)
            def update_ui():
                self.output_text.delete("1.0", tk.END)
                self.output_text.insert(tk.END, f"--- Output for '{command}' ---\n{result}")
                self.main_app.status_label.config(text="Command successful.")
            self.parent.after(0, update_ui)

class PhysicalLayerDiscovery(ttk.Frame):
    def __init__(self, parent, main_app_instance):
        super().__init__(parent)
        self.parent = parent
        self.main_app = main_app_instance
        self.create_widgets()

    def create_widgets(self):
        lldp_frame = ttk.LabelFrame(self, text="LLDP / CDP Discovery")
        lldp_frame.pack(padx=10, pady=10, fill="both", expand=True)
        control_frame = ttk.Frame(lldp_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        self.start_button = ttk.Button(control_frame, text="Start Scan", command=self.start_scan)
        self.start_button.pack(side="left", padx=5)
        self.stop_button = ttk.Button(control_frame, text="Stop Scan", command=self.stop_scan, state="disabled")
        self.stop_button.pack(side="left")
        self.progress = ttk.Progressbar(lldp_frame, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill="x", padx=5, pady=(0, 5))
        self.output_text = scrolledtext.ScrolledText(lldp_frame, wrap=tk.WORD, height=15)
        self.output_text.pack(padx=5, pady=5, fill="both", expand=True)

    def start_scan(self):
        self.output_text.delete("1.0", tk.END)
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress.start(10)
        self.main_app.status_label.config(text="Scanning for LLDP/CDP packets...")
        def update_output(message):
            self.parent.after(0, self._update_text_widget, message)
        net_tool.start_discovery_capture(update_output, timeout=60)
        self.output_text.insert(tk.END, "Scanning for LLDP/CDP packets (60s)...\n")

    def _update_text_widget(self, message):
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        if any(kw in message for kw in ["Found", "Scan complete", "requires", "Error"]):
            self.progress.stop()
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.main_app.status_label.config(text="Scan complete.")

    def stop_scan(self):
        net_tool.stop_discovery_capture()
        self.progress.stop()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.output_text.insert(tk.END, "\n--- Scan Stopped by User ---\n")
        self.main_app.status_label.config(text="Scan stopped by user.")

class MainApplication(tk.Window):
    """The main application window."""
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Network Triage Tool")
        self.geometry("600x750")

        status_bar = ttk.Frame(self)
        status_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 10))

        notebook = ttk.Notebook(self)
        notebook.pack(side="top", pady=10, padx=10, fill="both", expand=True)

        self.status_label = ttk.Label(status_bar, text="Ready")
        self.status_label.pack(side="left", padx=5)

        report_button = ttk.Button(status_bar, text="Save Report", command=self.save_report, bootstyle="secondary")
        report_button.pack(side="right")
        ToolTip(report_button, text="Gather all data from all tabs and save to a text file.")

        self.dashboard_tab = TriageDashboard(notebook, self)
        self.connection_tab = ConnectionDetails(notebook, self)
        self.performance_tab = PerformanceTab(notebook, self)
        self.connectivity_tab = ConnectivityTools(notebook, self)
        self.lldp_tab = PhysicalLayerDiscovery(notebook, self)
        self.advanced_tab = AdvancedDiagnostics(notebook, self)

        notebook.add(self.dashboard_tab, text="Dashboard")
        notebook.add(self.connection_tab, text="Connection")
        notebook.add(self.performance_tab, text="Performance")
        notebook.add(self.connectivity_tab, text="Connectivity")
        notebook.add(self.lldp_tab, text="Physical Layer")
        notebook.add(self.advanced_tab, text="Advanced")

    def save_report(self):
        """Gathers data from all tabs and saves it to a text file."""
        report_content = [
            "=" * 50, "NETWORK TRIAGE REPORT", f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}", "=" * 50 + "\n",
            "--- System & Network Information ---",
        ]
        for key, label in self.dashboard_tab.info_labels.items():
            report_content.append(f"{key}: {label.cget('text')}")
        report_content.append("\n" + "--- Connection Details ---")
        for key in self.connection_tab.detail_points:
            report_content.append(f"{key}: {self.connection_tab.detail_labels[key].cget('text')}")
        if self.connection_tab.detail_labels["Connection Type"].cget("text") == "Wi-Fi":
            for key in self.connection_tab.wifi_points:
                report_content.append(f"{key}: {self.connection_tab.detail_labels[key].cget('text')}")

        report_content.extend([
            "\n" + "--- User Notes ---",
            self.dashboard_tab.notes_text.get("1.0", tk.END).strip(),
            "\n" + "--- Connectivity Tools Output ---",
            "Ping Output:",
            self.connectivity_tab.ping_output_text.get("1.0", tk.END).strip(),
            "\nOther Tools Output:",
            self.connectivity_tab.other_tools_output.get("1.0", tk.END).strip(),
            "\n" + "--- Physical Layer (LLDP / CDP) Output ---",
            self.lldp_tab.output_text.get("1.0", tk.END).strip(),
            "\n" + "--- Advanced Diagnostics Output ---",
            self.advanced_tab.output_text.get("1.0", tk.END).strip(),
        ])

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Network Report",
            initialfile=f"network_report_{time.strftime('%Y-%m-%d_%H%M%S')}.txt",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(report_content))
                messagebox.showinfo("Success", f"Report saved to:\n{file_path}")
                self.status_label.config(text="Report saved.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report: {e}")
                self.status_label.config(text="Failed to save report.")

def main():
    """Main function to run the application."""
    app = MainApplication()
    app.mainloop()

if __name__ == "__main__":
    if platform.system() == "Darwin" and os.geteuid() != 0:
        try:
            python_executable, project_root = sys.executable, os.getcwd()
            command_to_run = f"cd '{project_root}' && '{python_executable}' -m src.macos.main_app"
            applescript = f'do shell script "{command_to_run}" with administrator privileges'
            subprocess.Popen(['osascript', '-e', applescript])
            sys.exit(0)
        except Exception as e:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Permissions Error", f"Could not relaunch with admin privileges.\n\nError: {e}")
            sys.exit("Administrator privileges are required.")

    main()
