from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label, Input, Button, Log, ContentSwitcher, DataTable, Select, TextArea
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive
import sys
import os
import platform
import ipaddress
import datetime

# ----------------------------------------------------------------------------
# OS-Agnostic Import (Selects the correct toolkit based on your OS)
# ----------------------------------------------------------------------------
current_os = platform.system()

if current_os == "Darwin":
    from .macos.network_toolkit import NetworkTriageToolkit
elif current_os == "Linux":
    from .linux.network_toolkit import NetworkTriageToolkit
elif current_os == "Windows":
    from .windows.network_toolkit import NetworkTriageToolkit
else:
    print(f"Unsupported OS: {current_os}")
    sys.exit(1)

net_tool = NetworkTriageToolkit()
# ----------------------------------------------------------------------------


class InfoBox(Static):
    title_text = reactive("Label")
    value_text = reactive("Loading...")

    def __init__(self, title, initial_value="", id=None):
        super().__init__(id=id)
        self.title_text = title
        if initial_value:
            self.value_text = initial_value

    def compose(self) -> ComposeResult:
        yield Label(self.title_text, classes="label-title")
        yield Label(self.value_text, classes="label-value")

    def watch_title_text(self, new_val):
        if not self.is_mounted: return
        self.query_one(".label-title", Label).update(new_val)

    def watch_value_text(self, new_val):
        if not self.is_mounted: return
        self.query_one(".label-value", Label).update(new_val)
    
    def on_click(self) -> None:
        """Copy value to clipboard on click."""
        val = self.value_text
        # Don't copy placeholder text
        if val and val not in ["N/A", "Loading...", "..."]:
            self.app.copy_to_clipboard(val)
            self.notify(f"Copied to clipboard: {val}", title="Clipboard", severity="information", timeout=2)


class Dashboard(Container):
    def compose(self) -> ComposeResult:
        yield InfoBox("Hostname", id="info_hostname")
        yield InfoBox("Operating System", id="info_os")
        yield InfoBox("Internal IP", id="info_internal_ip")
        yield InfoBox("Gateway", id="info_gateway")
        yield InfoBox("Public IP", id="info_public_ip")

    def on_mount(self):
        self.refresh_data()
        self.set_interval(60, self.refresh_data)

    @work(thread=True)
    def refresh_data(self):
        sys_info = net_tool.get_system_info()
        ip_info = net_tool.get_ip_info()
        self.app.call_from_thread(self._update_ui, sys_info, ip_info)

    def _update_ui(self, sys_info, ip_info):
        self.query_one("#info_hostname", InfoBox).value_text = sys_info.get("Hostname", "N/A")
        self.query_one("#info_os", InfoBox).value_text = sys_info.get("OS", "N/A")
        self.query_one("#info_internal_ip", InfoBox).value_text = ip_info.get("Internal IP", "N/A")
        self.query_one("#info_gateway", InfoBox).value_text = ip_info.get("Gateway", "N/A")
        self.query_one("#info_public_ip", InfoBox).value_text = ip_info.get("Public IP", "N/A")

class ConnectionTool(Container):
    """A tool to display detailed network interface information."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="tool_header"):
            yield Button("🔄 Refresh Connection Info", id="btn_refresh_conn", variant="default")
            yield Label("", id="conn_status")

        with Container(id="conn_grid"):
            yield InfoBox("Interface Name", id="iface_name")
            yield InfoBox("Type", id="iface_type")
            yield InfoBox("Status", id="iface_status")
            yield InfoBox("IP Address", id="iface_ip")
            yield InfoBox("MAC Address", id="iface_mac")
            yield InfoBox("Subnet Mask", id="iface_mask")
            yield InfoBox("Speed", id="iface_speed")
            yield InfoBox("MTU", id="iface_mtu")
            yield InfoBox("DNS Servers", id="iface_dns")
            
            yield InfoBox("Wi-Fi SSID", id="wifi_ssid")
            yield InfoBox("Channel", id="wifi_channel")
            yield InfoBox("Signal", id="wifi_signal")
            yield InfoBox("Noise", id="wifi_noise")

    def on_mount(self):
        self.refresh_connection()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_refresh_conn":
            self.refresh_connection()

    @work(thread=True)
    def refresh_connection(self):
        self.app.call_from_thread(
            self.query_one("#conn_status", Label).update, "Scanning interface..."
        )
        details = net_tool.get_connection_details()
        self.app.call_from_thread(self.update_ui, details)

    def update_ui(self, details):
        self.query_one("#conn_status", Label).update("Updated.")
        def set_val(widget_id, key):
            self.query_one(f"#{widget_id}", InfoBox).value_text = details.get(key, "N/A")

        set_val("iface_name", "Interface")
        set_val("iface_type", "Connection Type")
        set_val("iface_status", "Status")
        set_val("iface_ip", "IP Address")
        set_val("iface_mac", "MAC Address")
        set_val("iface_mask", "Netmask")
        set_val("iface_speed", "Speed")
        set_val("iface_mtu", "MTU")
        set_val("iface_dns", "DNS Servers")
        set_val("wifi_ssid", "SSID")
        set_val("wifi_channel", "Channel")
        set_val("wifi_signal", "Signal")
        set_val("wifi_noise", "Noise")

class PingTool(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(id="ping_controls"):
            yield Input(placeholder="Enter IP (e.g. 8.8.8.8)", id="ping_input")
            yield Button("▶ Start", id="start_ping_btn", variant="success")
            yield Button("⏹ Stop", id="stop_ping_btn", variant="error", disabled=True)
        yield Log(id="ping_log", highlight=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start_ping_btn":
            self.action_start_ping()
        elif event.button.id == "stop_ping_btn":
            self.action_stop_ping()

    def action_start_ping(self) -> None:
        host = self.query_one("#ping_input", Input).value
        if not host:
            self.notify("Please enter a valid IP", severity="error"); return
        self.query_one("#start_ping_btn", Button).disabled = True
        self.query_one("#stop_ping_btn", Button).disabled = False
        self.query_one("#ping_input", Input).disabled = True
        self.query_one("#ping_log", Log).clear()
        self.query_one("#ping_log", Log).write(f"--- Pinging {host} ---\n")
        self.start_ping_worker(host)

    def action_stop_ping(self) -> None:
        net_tool.stop_ping()
        self.workers.cancel_group(self, "ping_job")
        self.query_one("#ping_log", Log).write("\n--- Stopped ---\n")
        self.query_one("#start_ping_btn", Button).disabled = False
        self.query_one("#stop_ping_btn", Button).disabled = True
        self.query_one("#ping_input", Input).disabled = False

    @work(thread=True, group="ping_job")
    def start_ping_worker(self, host):
        def write_to_log(line):
            self.app.call_from_thread(self.query_one("#ping_log", Log).write, line)
        net_tool.continuous_ping(host, write_to_log)


class LLDPTool(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(classes="tool_header"):
            yield Button("Start Scan (60s)", id="btn_lldp_start", variant="success")
            yield Button("Stop", id="btn_lldp_stop", variant="error", disabled=True)
            yield Label("", id="lldp_status")
        
        yield Log(id="lldp_log", highlight=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_lldp_start":
            self.action_start_scan()
        elif event.button.id == "btn_lldp_stop":
            self.action_stop_scan()

    def action_start_scan(self) -> None:
        self.query_one("#btn_lldp_start", Button).disabled = True
        self.query_one("#btn_lldp_stop", Button).disabled = False
        self.query_one("#lldp_status", Label).update("Listening for packets...")
        
        log = self.query_one("#lldp_log", Log)
        log.clear()
        log.write("--- Starting LLDP/CDP Capture (60s timeout) ---\n")
        log.write("Note: This may require root/admin privileges to see packets.\n")

        self.start_lldp_worker()

    def action_stop_scan(self) -> None:
        self.scan_active = False 
        net_tool.stop_discovery_capture()
        self.query_one("#lldp_status", Label).update("Stopped.")
        self.query_one("#btn_lldp_start", Button).disabled = False
        self.query_one("#btn_lldp_stop", Button).disabled = True
        self.query_one("#lldp_log", Log).write("\n--- Scan Stopped ---\n")

    @work(thread=True)
    def start_lldp_worker(self):
        self.scan_active = True 
        def write_to_log(line):
            if "requires administrator privileges" in line:
                self.app.call_from_thread(
                    self.notify, 
                    "Error: Root/Admin rights needed for packet capture.", 
                    severity="error",
                    timeout=5
                )
            self.app.call_from_thread(self.update_log, line)
            
        net_tool.start_discovery_capture(write_to_log, timeout=60)
        
        if self.scan_active:
            self.app.call_from_thread(self.scan_finished)

    def update_log(self, line):
        self.query_one("#lldp_log", Log).write(line)

    def scan_finished(self):
        self.query_one("#btn_lldp_start", Button).disabled = False
        self.query_one("#btn_lldp_stop", Button).disabled = True
        self.query_one("#lldp_status", Label).update("Scan Complete.")

class SpeedTestTool(Container):
    def compose(self) -> ComposeResult:
        yield Button("🚀 Run Speed Test", id="btn_speed", variant="primary")
        yield Label("", id="speed_status")
        with Container(id="speed_results"):
            yield InfoBox("Download", id="spd_download")
            yield InfoBox("Upload", id="spd_upload")
            yield InfoBox("Ping", id="spd_ping")
            yield InfoBox("ISP", id="spd_isp")
            yield InfoBox("Server", id="spd_server")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_speed":
            self.start_test()

    def start_test(self):
        self.query_one("#btn_speed", Button).disabled = True
        self.query_one("#speed_status", Label).update("Running test...")
        for w in self.query(InfoBox): w.value_text = "..."
        self.run_speedtest_worker()

    @work(thread=True)
    def run_speedtest_worker(self):
        results = net_tool.run_speed_test()
        self.app.call_from_thread(self.display_results, results)

    def display_results(self, results):
        self.query_one("#btn_speed", Button).disabled = False
        self.query_one("#speed_status", Label).update("Done.")
        if "Error" in results:
            self.notify(results["Error"], severity="error")
            return
        self.query_one("#spd_download", InfoBox).value_text = results.get("Download", "N/A")
        self.query_one("#spd_upload", InfoBox).value_text = results.get("Upload", "N/A")
        self.query_one("#spd_ping", InfoBox).value_text = results.get("Ping", "N/A")
        self.query_one("#spd_isp", InfoBox).value_text = results.get("ISP", "N/A")
        self.query_one("#spd_server", InfoBox).value_text = results.get("Server", "N/A")


class NmapTool(Container):
    BINDINGS = [
        Binding("escape", "cancel_input", "Exit Input"),
    ]
    
    # Store results here for the Report Generator to find
    scan_data = []

    def compose(self) -> ComposeResult:
        with Horizontal(classes="tool_header"):
            yield Input(placeholder="Target IP/Subnet", id="nmap_input", classes="input_field")
            
            yield Select(
                options=[
                    ("Fast Scan (-F)", "-F"),
                    ("Intense Scan (-A -v)", "-A -v"),
                    ("Ping Scan (-sn)", "-sn"),
                    ("Custom Args", "custom"),
                ],
                allow_blank=False,
                value="-F",
                id="nmap_select"
            )
            
            yield Input(placeholder="Flags", value="-F", id="nmap_custom_args", classes="input_short hidden")
            
            yield Button("Start Scan", id="btn_nmap_start", variant="success")
        
        yield DataTable(id="nmap_table")

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("IP Address", "Hostname", "Status", "MAC Address", "Vendor")
        table.cursor_type = "row"
        self.detect_subnet_worker()

    def on_select_changed(self, event: Select.Changed) -> None:
        custom_input = self.query_one("#nmap_custom_args", Input)
        if event.value == "custom":
            custom_input.remove_class("hidden")
            custom_input.focus()
        else:
            custom_input.add_class("hidden")
            self.query_one("#nmap_select").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_nmap_start":
            self.action_start_scan()

    def action_cancel_input(self):
        self.query_one("#btn_nmap_start").focus()

    def on_input_submitted(self, event: Input.Submitted):
        self.action_start_scan()

    @work(thread=True)
    def detect_subnet_worker(self):
        details = net_tool.get_connection_details()
        ip = details.get("IP Address")
        mask = details.get("Netmask")

        if ip and mask and ip != "N/A":
            try:
                network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                self.app.call_from_thread(self.update_target_field, str(network))
            except ValueError:
                pass 

    def update_target_field(self, subnet):
        self.query_one("#nmap_input", Input).value = subnet

    def action_start_scan(self):
        target = self.query_one("#nmap_input", Input).value
        preset = self.query_one("#nmap_select", Select).value
        args = self.query_one("#nmap_custom_args", Input).value if preset == "custom" else preset
        
        if not target:
            self.notify("Please enter a target.", severity="error")
            return

        self.query_one("#btn_nmap_start", Button).disabled = True
        self.query_one(DataTable).clear()
        self.scan_data = [] # Clear old data
        self.notify(f"Starting scan: nmap {args} {target}")
        self.run_scan_worker(target, args)

    @work(thread=True)
    def run_scan_worker(self, target, args):
        results = net_tool.run_network_scan(target, args)
        self.app.call_from_thread(self.display_results, results)

    def display_results(self, results):
        self.query_one("#btn_nmap_start", Button).disabled = False
        table = self.query_one(DataTable)
        
        # Save for report
        self.scan_data = results
        
        if not results:
            self.notify("No hosts found.", severity="warning")
            return

        for host in results:
            if host.get('ip') == 'Error':
                self.notify(f"Scan Error: {host.get('status')}", severity="error")
                continue

            table.add_row(
                host.get('ip', 'N/A'),
                host.get('hostname', ''),
                host.get('status', 'up'),
                host.get('mac', ''),
                host.get('vendor', '')
            )
        self.notify("Scan Complete.")

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        """When a row is clicked, copy the IP Address (Column 0)."""
        table = self.query_one(DataTable)
        # Get the row data using the row_key from the event
        row_data = table.get_row(event.row_key)
        
        # Column 0 is the IP Address
        ip_addr = row_data[0]
        
        if ip_addr and ip_addr != "N/A":
            self.app.copy_to_clipboard(ip_addr)
            self.notify(f"Copied IP: {ip_addr}", title="Clipboard", severity="information")


# ----------------------------------------------------------------------------
# Notes Tool (New)
# ----------------------------------------------------------------------------
class NotesTool(Container):
    def compose(self) -> ComposeResult:
        yield Label("📝 Engineer Notes / Observations", id="notes_header")
        yield TextArea(id="notes_area", language=None)

# ----------------------------------------------------------------------------
# Utility Tools (Traceroute, DNS, Port Check)
# ----------------------------------------------------------------------------

class TracerouteTool(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(classes="tool_header"):
            yield Input(placeholder="Host (e.g. google.com)", id="trace_input", classes="input_field")
            yield Button("Run Trace", id="btn_trace", variant="warning")
        yield Log(id="trace_log", highlight=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_trace":
            self.action_run_trace()
            
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Run when Enter is pressed."""
        self.action_run_trace()

    def action_run_trace(self):
        host = self.query_one("#trace_input", Input).value
        if not host:
            self.notify("Please enter a host.", severity="error"); return
            
        log = self.query_one("#trace_log", Log)
        log.clear()
        log.write(f"--- Starting Traceroute to {host} ---\n")
        log.write("This may take up to 45 seconds. Please wait...\n")
        
        self.query_one("#btn_trace", Button).disabled = True
        self.run_trace_worker(host)

    @work(thread=True)
    def run_trace_worker(self, host):
        result = net_tool.traceroute_test(host)
        self.app.call_from_thread(self.display_result, result)

    def display_result(self, result):
        self.query_one("#btn_trace", Button).disabled = False
        self.query_one("#trace_log", Log).write(result)
        self.query_one("#trace_log", Log).write("\n--- Finished ---")


class DNSTool(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(classes="tool_header"):
            yield Input(placeholder="Domain (e.g. google.com)", id="dns_input", classes="input_field")
            yield Button("Resolve IP", id="btn_dns", variant="warning")
        yield Label("Result will appear here...", id="dns_result", classes="result_box")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_dns":
            self.action_resolve()
            
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Run when Enter is pressed."""
        self.action_resolve()

    def action_resolve(self):
        domain = self.query_one("#dns_input", Input).value
        if not domain:
            self.notify("Please enter a domain.", severity="error"); return
            
        self.query_one("#dns_result", Label).update("Resolving...")
        self.resolve_worker(domain)

    @work(thread=True)
    def resolve_worker(self, domain):
        result = net_tool.dns_resolution_test(domain)
        self.app.call_from_thread(self.query_one("#dns_result", Label).update, result)


class PortTool(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(id="port_form"):
            yield Input(placeholder="Host/IP", id="port_host")
            yield Input(placeholder="Port", id="port_num")
            yield Button("Check Port", id="btn_port", variant="warning")
        yield Label("Result will appear here...", id="port_result", classes="result_box")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_port":
            self.action_check()
            
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Run when Enter is pressed."""
        self.action_check()

    def action_check(self):
        host = self.query_one("#port_host", Input).value
        port = self.query_one("#port_num", Input).value
        
        if not host or not port:
            self.notify("Please enter Host and Port.", severity="error"); return
            
        self.query_one("#port_result", Label).update(f"Checking {host}:{port}...")
        self.check_worker(host, port)

    @work(thread=True)
    def check_worker(self, host, port):
        result = net_tool.port_connectivity_test(host, port)
        self.app.call_from_thread(self.query_one("#port_result", Label).update, result)


class UtilityTool(Container):
    """Holds the 3 sub-tools with a manual switcher."""
    
    def compose(self) -> ComposeResult:
        # Internal Navigation Bar
        with Horizontal(id="util_nav"):
            yield Button("Traceroute", id="sub_trace", classes="util_btn")
            yield Button("DNS Lookup", id="sub_dns", classes="util_btn")
            yield Button("Port Check", id="sub_port", classes="util_btn")
        
        # Content Switcher for Sub-Tools
        with ContentSwitcher(initial="tool_trace", id="util_content"):
            yield TracerouteTool(id="tool_trace")
            yield DNSTool(id="tool_dns")
            yield PortTool(id="tool_port")

    def on_mount(self):
        self.query_one("#sub_trace").add_class("-active")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id and btn_id.startswith("sub_"):
            target_map = {
                "sub_trace": "tool_trace",
                "sub_dns": "tool_dns",
                "sub_port": "tool_port"
            }
            if btn_id in target_map:
                # Switch Content
                self.query_one("#util_content", ContentSwitcher).current = target_map[btn_id]
                # Update Buttons
                for btn in self.query(".util_btn"): btn.remove_class("-active")
                self.query_one(f"#{btn_id}", Button).add_class("-active")

class NetworkTriageApp(App):
    """A Textual TUI with Manual Button Navigation."""

    CSS_PATH = "triage.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+s", "save_report", "Save Report"),
        Binding("d", "switch_tab('dashboard')", "Dashboard"),
        Binding("c", "switch_tab('connection')", "Connection"),
        Binding("s", "switch_tab('speed')", "Speed Test"),
        Binding("p", "switch_tab('ping')", "Ping"),
        Binding("l", "switch_tab('lldp')", "LLDP Scan"),
        Binding("n", "switch_tab('nmap')", "Nmap Scan"),
        Binding("o", "switch_tab('notes')", "Notes"),
        Binding("u", "switch_tab('utils')", "Utilities"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="nav_bar"):
            yield Button("📊 Dashboard", id="tab_dashboard", classes="nav_btn")
            yield Button("🔌 Connection", id="tab_connection", classes="nav_btn")
            yield Button("🚀 Speed", id="tab_speed", classes="nav_btn")
            yield Button("📡 Ping", id="tab_ping", classes="nav_btn")
            yield Button("🔍 LLDP", id="tab_lldp", classes="nav_btn")
            yield Button("🌐 Nmap", id="tab_nmap", classes="nav_btn")
            yield Button("📝 Notes", id="tab_notes", classes="nav_btn")
            yield Button("🛠️ Utils", id="tab_utils", classes="nav_btn")

        with ContentSwitcher(initial="dashboard", id="content_box"):
            yield Dashboard(id="dashboard")
            yield ConnectionTool(id="connection")
            yield SpeedTestTool(id="speed")
            yield PingTool(id="ping")
            yield LLDPTool(id="lldp")
            yield NmapTool(id="nmap")
            yield NotesTool(id="notes")
            yield UtilityTool(id="utils")

        yield Footer()

    def on_mount(self):
        self.query_one("#tab_dashboard").add_class("-active")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id and btn_id.startswith("tab_"):
            target_id = btn_id.replace("tab_", "")
            self.action_switch_tab(target_id)

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one("#content_box", ContentSwitcher).current = tab_id
        for btn in self.query(".nav_btn"):
            btn.remove_class("-active")
        self.query_one(f"#tab_{tab_id}", Button).add_class("-active")

    def action_save_report(self):
        """Gathers data from all widgets and saves to a file."""
        self.notify("Generating report...")
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Triage_Report_{timestamp}.txt"
        
        # 1. Gather Dashboard Info
        dash = self.query_one(Dashboard)
        hostname = dash.query_one("#info_hostname", InfoBox).value_text
        os_sys = dash.query_one("#info_os", InfoBox).value_text
        int_ip = dash.query_one("#info_internal_ip", InfoBox).value_text
        pub_ip = dash.query_one("#info_public_ip", InfoBox).value_text
        
        # 2. Gather Connection Details
        conn = self.query_one(ConnectionTool)
        # Helper to extract value safely
        def get_conn(idx): return conn.query_one(f"#{idx}", InfoBox).value_text
        
        # 3. Gather Speed Test
        speed = self.query_one(SpeedTestTool)
        dl = speed.query_one("#spd_download", InfoBox).value_text
        ul = speed.query_one("#spd_upload", InfoBox).value_text
        ping = speed.query_one("#spd_ping", InfoBox).value_text
        
        # 4. Gather Nmap Data (from our new class variable)
        nmap_tool = self.query_one(NmapTool)
        scan_data = nmap_tool.scan_data
        
        # 5. Gather Notes
        notes = self.query_one("#notes_area", TextArea).text

        # Build the Report String
        report = []
        report.append("="*50)
        report.append(f"NETWORK TRIAGE REPORT - {timestamp}")
        report.append("="*50 + "\n")
        
        report.append(f"SYSTEM INFO")
        report.append(f"Hostname:    {hostname}")
        report.append(f"OS:          {os_sys}")
        report.append(f"Internal IP: {int_ip}")
        report.append(f"Public IP:   {pub_ip}\n")
        
        report.append(f"CONNECTION DETAILS")
        report.append(f"Interface:   {get_conn('iface_name')}")
        report.append(f"Type:        {get_conn('iface_type')}")
        report.append(f"Status:      {get_conn('iface_status')}")
        report.append(f"Speed/MTU:   {get_conn('iface_speed')} / {get_conn('iface_mtu')}")
        report.append(f"DNS:         {get_conn('iface_dns')}")
        if get_conn('wifi_ssid') != "N/A":
            report.append(f"Wi-Fi:       {get_conn('wifi_ssid')} (Ch: {get_conn('wifi_channel')})")
        report.append("")
        
        if dl != "...":
            report.append(f"SPEED TEST")
            report.append(f"Download:    {dl}")
            report.append(f"Upload:      {ul}")
            report.append(f"Ping:        {ping}\n")
            
        if scan_data:
            report.append(f"NMAP SCAN RESULTS")
            report.append(f"{'IP':<16} {'HOSTNAME':<25} {'STATUS':<10} {'VENDOR'}")
            report.append("-" * 70)
            for host in scan_data:
                ip = host.get('ip', 'N/A')
                name = host.get('hostname', '')[:24] # Truncate long names
                status = host.get('status', '')
                vendor = host.get('vendor', '')
                report.append(f"{ip:<16} {name:<25} {status:<10} {vendor}")
            report.append("")

        if notes.strip():
            report.append(f"USER NOTES")
            report.append("-" * 50)
            report.append(notes)
            report.append("-" * 50)
            
        # Write to file
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(report))
            self.notify(f"Report saved to {filename}", severity="information", timeout=5)
        except Exception as e:
            self.notify(f"Failed to save: {e}", severity="error")


def run():
    """Entry point for the console script."""
    app = NetworkTriageApp()
    app.run()

if __name__ == "__main__":
    run()