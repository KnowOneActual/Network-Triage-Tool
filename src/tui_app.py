from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label, Input, Button, Log, ContentSwitcher
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual.reactive import reactive

import sys
import os

sys.path.append(os.getcwd())

from src.macos.network_toolkit import NetworkTriageToolkit

net_tool = NetworkTriageToolkit()

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

        # Using a Scrollable container because this list can get long
        with Container(id="conn_grid"):
            # Standard Interface Info
            yield InfoBox("Interface Name", id="iface_name")
            yield InfoBox("Type", id="iface_type")
            yield InfoBox("Status", id="iface_status")
            yield InfoBox("IP Address", id="iface_ip")
            yield InfoBox("MAC Address", id="iface_mac")
            yield InfoBox("Subnet Mask", id="iface_mask")
            yield InfoBox("Speed", id="iface_speed")
            yield InfoBox("MTU", id="iface_mtu")
            yield InfoBox("DNS Servers", id="iface_dns")
            
            # Wi-Fi Specific Info (Will display N/A for Ethernet)
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
        
        # Fetch the heavy data
        details = net_tool.get_connection_details()
        
        self.app.call_from_thread(self.update_ui, details)

    def update_ui(self, details):
        self.query_one("#conn_status", Label).update("Updated.")
        
        # Helper to safely get keys or show "N/A"
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
        
        # Wi-Fi (Might be missing if Ethernet)
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
    """A tool to capture LLDP and CDP packets."""

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
        net_tool.stop_discovery_capture()
        self.query_one("#lldp_status", Label).update("Stopped.")
        self.query_one("#btn_lldp_start", Button).disabled = False
        self.query_one("#btn_lldp_stop", Button).disabled = True
        self.query_one("#lldp_log", Log).write("\n--- Scan Stopped ---\n")

    @work(thread=True)
    def start_lldp_worker(self):
        self.scan_active = True # Track state
        
        def write_to_log(line):
            # Check for permission errors
            if "requires administrator privileges" in line:
                self.app.call_from_thread(
                    self.notify, 
                    "Error: Root/Admin rights needed for packet capture.", 
                    severity="error",
                    timeout=5
                )
            self.app.call_from_thread(self.update_log, line)
            
        # Run the capture
        net_tool.start_discovery_capture(write_to_log, timeout=60)
        
        # Only show "Scan Complete" if we didn't stop it manually
        if self.scan_active:
            self.app.call_from_thread(self.scan_finished)

    def action_stop_scan(self) -> None:
        self.scan_active = False # Flag that we stopped it manually
        net_tool.stop_discovery_capture()
        self.query_one("#lldp_status", Label).update("Stopped.")
        self.query_one("#btn_lldp_start", Button).disabled = False
        self.query_one("#btn_lldp_stop", Button).disabled = True
        self.query_one("#lldp_log", Log).write("\n--- Scan Stopped ---\n")

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


class NetworkTriageApp(App):
    """A Textual TUI with Manual Button Navigation."""

    CSS_PATH = "triage.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "switch_tab('dashboard')", "Dashboard"),
        Binding("c", "switch_tab('connection')", "Connection"),
        Binding("s", "switch_tab('speed')", "Speed Test"),
        Binding("p", "switch_tab('ping')", "Ping"),
        Binding("l", "switch_tab('lldp')", "LLDP Scan"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        # --- MANUAL TAB BAR ---
        # No magic widgets. Just a row of buttons.
        with Horizontal(id="nav_bar"):
            yield Button("📊 Dashboard", id="tab_dashboard", classes="nav_btn")
            yield Button("🔌 Connection", id="tab_connection", classes="nav_btn")
            yield Button("🚀 Speed Test", id="tab_speed", classes="nav_btn")
            yield Button("📡 Ping", id="tab_ping", classes="nav_btn")
            yield Button("🔍 LLDP", id="tab_lldp", classes="nav_btn")

        # --- CONTENT SWITCHER ---
        # Holds the actual pages. We manually tell it which one to show.
        with ContentSwitcher(initial="dashboard", id="content_box"):
            yield Dashboard(id="dashboard")
            yield ConnectionTool(id="connection")
            yield SpeedTestTool(id="speed")
            yield PingTool(id="ping")
            yield LLDPTool(id="lldp")

        yield Footer()

    def on_mount(self):
        # Set initial active tab styling
        self.query_one("#tab_dashboard").add_class("-active")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle clicks on the nav bar."""
        btn_id = event.button.id
        if btn_id and btn_id.startswith("tab_"):
            # Extract 'dashboard' from 'tab_dashboard'
            target_id = btn_id.replace("tab_", "")
            self.action_switch_tab(target_id)

    def action_switch_tab(self, tab_id: str) -> None:
        """Manually switch content and update button styles."""
        # 1. Switch the content
        self.query_one("#content_box", ContentSwitcher).current = tab_id
        
        # 2. Update button styles (visual feedback)
        # Remove '-active' from ALL nav buttons
        for btn in self.query(".nav_btn"):
            btn.remove_class("-active")
        
        # Add '-active' to the specific button
        self.query_one(f"#tab_{tab_id}", Button).add_class("-active")

if __name__ == "__main__":
    app = NetworkTriageApp()
    app.run()