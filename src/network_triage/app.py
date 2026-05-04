from __future__ import annotations

import datetime
import importlib.metadata
import ipaddress
import platform
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .shared.shared_toolkit import NetworkToolkit

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import (
    Button,
    ContentSwitcher,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Log,
    ProgressBar,
    Select,
    Static,
    TextArea,
)

# Phase 4 Widgets
try:
    from tui.widgets import (
        ConnectionMonitorWidget,
        DNSResolverWidget,
        LanBandwidthWidget,
        LatencyAnalyzerWidget,
        PortScannerWidget,
    )
    from tui.widgets.base import TaskCompleted
    from tui.widgets.components import HistoryInput
except ImportError:
    # Fallback for local development if tui is not in path correctly
    sys.path.append(str(sys.path[0] + "/.."))
    from tui.widgets import (
        ConnectionMonitorWidget,
        DNSResolverWidget,
        LanBandwidthWidget,
        LatencyAnalyzerWidget,
        PortScannerWidget,
    )
    from tui.widgets.base import TaskCompleted
    from tui.widgets.components import HistoryInput

# ----------------------------------------------------------------------------
# OS-Agnostic Import (Selects the correct toolkit based on your OS)
# ----------------------------------------------------------------------------
current_os = platform.system()

match current_os:
    case "Darwin":
        from .macos.network_toolkit import NetworkTriageToolkit
    case "Linux":
        from .linux.network_toolkit import NetworkTriageToolkit  # type: ignore[assignment]
    case "Windows":
        from .windows.network_toolkit import NetworkTriageToolkit  # type: ignore[assignment]
    case _:
        sys.stderr.write(f"Unsupported OS: {current_os}\n")
        sys.exit(1)

net_tool: NetworkToolkit = NetworkTriageToolkit()
# ----------------------------------------------------------------------------


class InfoBox(Static):
    title_text = reactive("Label")
    value_text = reactive("Waiting to run ...")

    def __init__(self, title: str, initial_value: str = "", id: str | None = None) -> None:
        super().__init__(id=id)
        self.title_text = title
        if initial_value:
            self.value_text = initial_value

    def compose(self) -> ComposeResult:
        yield Label(self.title_text, classes="label-title")
        yield Label(self.value_text, classes="label-value")

    def watch_title_text(self, new_val: str) -> None:
        if not self.is_mounted:
            return
        self.query_one(".label-title", Label).update(new_val)

    def watch_value_text(self, new_val: str) -> None:
        if not self.is_mounted:
            return
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
        yield InfoBox("Toolkit Health", id="info_health")

    def on_mount(self) -> None:
        self.refresh_data()
        self.set_interval(60, self.refresh_data)

    @work(thread=True)
    def refresh_data(self) -> None:
        sys_info = net_tool.get_system_info()
        ip_info = net_tool.get_ip_info()
        health = net_tool.health_check()
        self.app.call_from_thread(self._update_ui, sys_info, ip_info, health)

    def _update_ui(self, sys_info: dict[str, str], ip_info: dict[str, str], health: dict[str, Any]) -> None:
        self.query_one("#info_hostname", InfoBox).value_text = sys_info.get("Hostname", "N/A")
        self.query_one("#info_os", InfoBox).value_text = sys_info.get("OS", "N/A")
        self.query_one("#info_internal_ip", InfoBox).value_text = ip_info.get("Internal IP", "N/A")
        self.query_one("#info_gateway", InfoBox).value_text = ip_info.get("Gateway", "N/A")
        self.query_one("#info_public_ip", InfoBox).value_text = ip_info.get("Public IP", "N/A")
        self.query_one("#info_health", InfoBox).value_text = health.get("status", "N/A")


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

    def on_mount(self) -> None:
        self.refresh_connection()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn_refresh_conn":
                self.refresh_connection()

    @work(thread=True)
    def refresh_connection(self) -> None:
        self.app.call_from_thread(self.query_one("#conn_status", Label).update, "Scanning interface...")
        details = net_tool.get_connection_details()
        self.app.call_from_thread(self.update_ui, details)

    def update_ui(self, details: dict[str, str]) -> None:
        self.query_one("#conn_status", Label).update("Updated.")

        def set_val(widget_id: str, key: str) -> None:
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
            yield HistoryInput(placeholder="Enter IP (e.g. 8.8.8.8)", id="ping_input")
            yield Button("▶ Start", id="start_ping_btn", variant="success")
            yield Button("⏹ Stop", id="stop_ping_btn", variant="error", disabled=True)
        yield Log(id="ping_log", highlight=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "start_ping_btn":
                self.action_start_ping()
            case "stop_ping_btn":
                self.action_stop_ping()

    def action_start_ping(self) -> None:
        host_input = self.query_one("#ping_input", HistoryInput)
        host = host_input.value
        if not host:
            self.notify("Please enter a valid IP", severity="error")
            return
        host_input.push_history(host)
        self.query_one("#start_ping_btn", Button).disabled = True
        self.query_one("#stop_ping_btn", Button).disabled = False
        self.query_one("#ping_input", HistoryInput).disabled = True
        self.query_one("#ping_log", Log).clear()
        self.query_one("#ping_log", Log).write(f"--- Pinging {host} ---\n")
        self.start_ping_worker(host)

    def action_stop_ping(self) -> None:
        net_tool.stop_ping()
        self.workers.cancel_group(self, "ping_job")
        self.query_one("#ping_log", Log).write("\n--- Stopped ---\n")
        self.query_one("#start_ping_btn", Button).disabled = False
        self.query_one("#stop_ping_btn", Button).disabled = True
        self.query_one("#ping_input", HistoryInput).disabled = False

        # Ping is manually stopped, but we can still count it as a "completed" task session
        self.post_message(TaskCompleted("ping"))

    @work(thread=True, group="ping_job")
    def start_ping_worker(self, host: str) -> None:
        def write_to_log(line: str) -> None:
            self.app.call_from_thread(self.query_one("#ping_log", Log).write, line)

        net_tool.continuous_ping(host, write_to_log)


class LLDPTool(Container):
    scan_active: bool = False

    def compose(self) -> ComposeResult:
        with Horizontal(classes="tool_header"):
            yield Button("Start Scan (60s)", id="btn_lldp_start", variant="success")
            yield Button("Stop", id="btn_lldp_stop", variant="error", disabled=True)
            yield Label("", id="lldp_status")

        yield Log(id="lldp_log", highlight=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn_lldp_start":
                self.action_start_scan()
            case "btn_lldp_stop":
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
    def start_lldp_worker(self) -> None:
        self.scan_active = True

        def write_to_log(line: str) -> None:
            if "requires administrator privileges" in line:
                self.app.call_from_thread(
                    self.notify,
                    "Error: Root/Admin rights needed for packet capture.",
                    severity="error",
                    timeout=5,
                )
            self.app.call_from_thread(self.update_log, line)

        net_tool.start_discovery_capture(write_to_log, timeout=60)

        if self.scan_active:
            self.app.call_from_thread(self.scan_finished)

    def update_log(self, line: str) -> None:
        self.query_one("#lldp_log", Log).write(line)

    def scan_finished(self) -> None:
        self.query_one("#btn_lldp_start", Button).disabled = False
        self.query_one("#btn_lldp_stop", Button).disabled = True
        self.query_one("#lldp_status", Label).update("Scan Complete.")


class SpeedTestTool(Container):
    def compose(self) -> ComposeResult:
        yield Button("🚀 Run Speed Test", id="btn_speed", variant="primary")
        # Indeterminate progress bar (total=None means it pulses)
        yield ProgressBar(id="speed_progress", total=None, show_eta=False, classes="hidden")
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

    def start_test(self) -> None:
        self.query_one("#btn_speed", Button).disabled = True
        self.query_one("#speed_status", Label).update("Running test (this may take 20-30s)...")

        # Show and start animation
        bar = self.query_one("#speed_progress", ProgressBar)
        bar.remove_class("hidden")

        for w in self.query(InfoBox):
            w.value_text = "..."
        self.run_speedtest_worker()

    @work(thread=True)
    def run_speedtest_worker(self) -> None:
        results = net_tool.run_speed_test()
        self.app.call_from_thread(self.display_results, results)

    def display_results(self, results: dict[str, str]) -> None:
        self.query_one("#btn_speed", Button).disabled = False

        # Hide animation
        bar = self.query_one("#speed_progress", ProgressBar)
        bar.add_class("hidden")

        self.query_one("#speed_status", Label).update("Done.")
        if "Error" in results:
            self.notify(results["Error"], severity="error")
            return

        # Helper to set values
        def set_val(uid: str, key: str) -> None:
            self.query_one(f"#{uid}", InfoBox).value_text = results.get(key, "N/A")

        set_val("spd_download", "Download")
        set_val("spd_upload", "Upload")
        set_val("spd_ping", "Ping")
        set_val("spd_isp", "ISP")
        set_val("spd_server", "Server")


class NmapTool(Container):
    BINDINGS = [
        Binding("escape", "cancel_input", "Exit Input"),
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.scan_data: list[dict[str, str]] = []

    def compose(self) -> ComposeResult:
        with Horizontal(classes="tool_header"):
            yield HistoryInput(placeholder="Target IP/Subnet", id="nmap_input", classes="input_field")

            yield Select(
                options=[
                    ("Fast Scan (-F)", "-F"),
                    ("Intense Scan (-A -v)", "-A -v"),
                    ("Ping Scan (-sn)", "-sn"),
                    ("Custom Args", "custom"),
                ],
                allow_blank=False,
                value="-F",
                id="nmap_select",
            )

            yield Input(placeholder="Flags", value="-F", id="nmap_custom_args", classes="input_short hidden")

            yield Button("Start Scan", id="btn_nmap_start", variant="success")

        # Progress bar between header and table
        yield ProgressBar(id="nmap_progress", total=None, show_eta=False, classes="hidden")
        yield DataTable(id="nmap_table")

    def on_mount(self) -> None:
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

    def action_cancel_input(self) -> None:
        self.query_one("#btn_nmap_start").focus()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        self.action_start_scan()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """When a row is clicked, copy the IP Address (Column 0)."""
        table = self.query_one(DataTable)
        row_data = table.get_row(event.row_key)
        ip_addr = row_data[0]

        if ip_addr and ip_addr != "N/A":
            self.app.copy_to_clipboard(ip_addr)
            self.notify(f"Copied IP: {ip_addr}", title="Clipboard", severity="information")

    @work(thread=True)
    def detect_subnet_worker(self) -> None:
        details = net_tool.get_connection_details()
        ip = details.get("IP Address")
        mask = details.get("Netmask")

        if ip and mask and ip != "N/A":
            try:
                network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                self.app.call_from_thread(self.update_target_field, str(network))
            except ValueError:
                pass

    def update_target_field(self, subnet: str) -> None:
        self.query_one("#nmap_input", HistoryInput).value = subnet

    def action_start_scan(self) -> None:
        target_input = self.query_one("#nmap_input", HistoryInput)
        target = target_input.value
        preset = self.query_one("#nmap_select", Select).value
        args = self.query_one("#nmap_custom_args", Input).value if preset == "custom" else preset

        if not target:
            self.notify("Please enter a target.", severity="error")
            return

        target_input.push_history(target)
        self.query_one("#btn_nmap_start", Button).disabled = True
        self.query_one(DataTable).clear()
        self.scan_data = []

        # Start Progress Bar
        bar = self.query_one("#nmap_progress", ProgressBar)
        bar.remove_class("hidden")

        self.notify(f"Starting scan: nmap {args} {target}")
        self.run_scan_worker(target, args)

    @work(thread=True)
    def run_scan_worker(self, target: str, args: str) -> None:
        results = net_tool.run_network_scan(target, args)
        self.app.call_from_thread(self.display_results, results)

    def display_results(self, results: list[dict[str, str]]) -> None:
        self.query_one("#btn_nmap_start", Button).disabled = False

        # Stop Progress Bar
        bar = self.query_one("#nmap_progress", ProgressBar)
        bar.add_class("hidden")

        table = self.query_one(DataTable)
        self.scan_data = results

        if not results:
            self.notify("No hosts found.", severity="warning")
            return

        for host in results:
            if host.get("ip") == "Error":
                self.notify(f"Scan Error: {host.get('status')}", severity="error")
                continue

            table.add_row(
                host.get("ip", "N/A"),
                host.get("hostname", ""),
                host.get("status", "up"),
                host.get("mac", ""),
                host.get("vendor", ""),
            )
        self.notify("Scan Complete.")
        self.post_message(TaskCompleted("nmap"))


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

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        """Run when Enter is pressed."""
        self.action_run_trace()

    def action_run_trace(self) -> None:
        host = self.query_one("#trace_input", Input).value
        if not host:
            self.notify("Please enter a host.", severity="error")
            return

        log = self.query_one("#trace_log", Log)
        log.clear()
        log.write(f"--- Starting Traceroute to {host} ---\n")
        log.write("This may take up to 45 seconds. Please wait...\n")

        self.query_one("#btn_trace", Button).disabled = True
        self.run_trace_worker(host)

    @work(thread=True)
    def run_trace_worker(self, host: str) -> None:
        result = net_tool.traceroute_test(host)
        self.app.call_from_thread(self.display_result, result)

    def display_result(self, result: str) -> None:
        self.query_one("#btn_trace", Button).disabled = False
        self.query_one("#trace_log", Log).write(result)
        self.query_one("#trace_log", Log).write("\n--- Finished ---")


class UtilityTool(Container):
    """Holds the sub-tools with a manual switcher."""

    def compose(self) -> ComposeResult:
        # Internal Navigation Bar
        with Horizontal(id="util_nav"):
            yield Button("Traceroute", id="sub_trace", classes="util_btn")
            yield Button("DNS Resolver", id="sub_dns", classes="util_btn")
            yield Button("Port Scanner", id="sub_port", classes="util_btn")
            yield Button("Latency Analyzer", id="sub_latency", classes="util_btn")
            yield Button("Connection Monitor", id="sub_connmon", classes="util_btn")
            yield Button("LAN Bandwidth", id="sub_bandwidth", classes="util_btn")

        # Content Switcher for Sub-Tools
        with ContentSwitcher(initial="tool_trace", id="util_content"):
            yield TracerouteTool(id="tool_trace")
            yield DNSResolverWidget(id="tool_dns")
            yield PortScannerWidget(id="tool_port")
            yield LatencyAnalyzerWidget(id="tool_latency")
            yield ConnectionMonitorWidget(id="tool_connmon")
            yield LanBandwidthWidget(id="tool_bandwidth")

    def on_mount(self) -> None:
        self.query_one("#sub_trace").add_class("-active")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id and btn_id.startswith("sub_"):
            target_map = {
                "sub_trace": "tool_trace",
                "sub_dns": "tool_dns",
                "sub_port": "tool_port",
                "sub_latency": "tool_latency",
                "sub_connmon": "tool_connmon",
                "sub_bandwidth": "tool_bandwidth",
            }
            if btn_id in target_map:
                # Switch Content
                self.query_one("#util_content", ContentSwitcher).current = target_map[btn_id]
                # Update Buttons
                for btn in self.query(".util_btn"):
                    btn.remove_class("-active")
                self.query_one(f"#{btn_id}", Button).add_class("-active")

                # Clear notification dot when switching to this sub-tab
                btn = event.button
                btn.label = str(btn.label).replace(" •", "")

    def on_task_completed(self, event: TaskCompleted) -> None:
        """Update sub-navigation badges when a utility task finishes in background."""
        current_sub = self.query_one("#util_content", ContentSwitcher).current
        sub_map = {
            "tool_trace": "sub_trace",
            "tool_dns": "sub_dns",
            "tool_port": "sub_port",
            "tool_latency": "sub_latency",
            "tool_connmon": "sub_connmon",
            "tool_bandwidth": "sub_bandwidth",
        }

        widget_id = event.widget_id or ""
        target_sub_btn = None
        # Handle exact match or ends-with for ID with prefix
        for wid, bid in sub_map.items():
            if widget_id == wid or (widget_id and widget_id.endswith(wid)):
                target_sub_btn = bid
                break

        if target_sub_btn and current_sub and sub_map.get(str(current_sub)) != target_sub_btn:
            btn = self.query_one(f"#{target_sub_btn}", Button)
            label_str = str(btn.label)
            if "•" not in label_str:
                btn.label = f"{label_str} •"


class NetworkTriageApp(App[None]):
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

    def on_mount(self) -> None:
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
        btn = self.query_one(f"#tab_{tab_id}", Button)
        btn.add_class("-active")

        # Clear notification dot when switching to this tab
        btn.label = str(btn.label).replace(" •", "")

    def on_task_completed(self, event: TaskCompleted) -> None:
        """Handle background task completion and update badges."""
        current_tab = self.query_one("#content_box", ContentSwitcher).current

        # Mapping from widget ID to tab ID
        tab_map = {
            "dashboard": "dashboard",
            "connection": "connection",
            "speed": "speed",
            "ping": "ping",
            "lldp": "lldp",
            "nmap": "nmap",
            "notes": "notes",
            "tool_trace": "utils",
            "tool_dns": "utils",
            "tool_port": "utils",
            "tool_latency": "utils",
            "tool_connmon": "utils",
            "tool_bandwidth": "utils",
        }

        # Determine which tab the widget belongs to
        widget_id = event.widget_id or ""
        target_tab = None
        for wid, tid in tab_map.items():
            if widget_id == wid or (widget_id and widget_id.endswith(wid)):
                target_tab = tid
                break

        if target_tab and target_tab != current_tab:
            # Update navigation button with a dot
            btn = self.query_one(f"#tab_{target_tab}", Button)
            label_str = str(btn.label)
            if "•" not in label_str:
                btn.label = f"{label_str} •"

        # Also bubble down to UtilityTool if relevant
        if target_tab == "utils":
            try:
                util_tool = self.query_one(UtilityTool)
                util_tool.on_task_completed(event)
            except Exception:
                pass

    def action_save_report(self) -> None:
        """Gathers data from all widgets and saves to a file."""
        self.notify("Generating report...")

        timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Triage_Report_{timestamp}.txt"

        # Gather all data
        dashboard_data = self._gather_dashboard_data()
        connection_data = self._gather_connection_data()
        speed_data = self._gather_speed_data()
        nmap_data = self._gather_nmap_data()
        notes = self._gather_notes()

        # Build the report
        report = self._build_report(timestamp, dashboard_data, connection_data, speed_data, nmap_data, notes)

        # Write to file
        self._write_report(filename, report)

    def _gather_dashboard_data(self) -> dict[str, str]:
        """Gather dashboard information."""
        dash = self.query_one(Dashboard)
        return {
            "hostname": dash.query_one("#info_hostname", InfoBox).value_text,
            "os_sys": dash.query_one("#info_os", InfoBox).value_text,
            "int_ip": dash.query_one("#info_internal_ip", InfoBox).value_text,
            "pub_ip": dash.query_one("#info_public_ip", InfoBox).value_text,
        }

    def _gather_connection_data(self) -> dict[str, str]:
        """Gather connection details."""
        conn = self.query_one(ConnectionTool)

        def get_conn(idx: str) -> str:
            return conn.query_one(f"#{idx}", InfoBox).value_text

        return {
            "iface_name": get_conn("iface_name"),
            "iface_type": get_conn("iface_type"),
            "iface_status": get_conn("iface_status"),
            "iface_speed": get_conn("iface_speed"),
            "iface_mtu": get_conn("iface_mtu"),
            "iface_dns": get_conn("iface_dns"),
            "wifi_ssid": get_conn("wifi_ssid"),
            "wifi_channel": get_conn("wifi_channel"),
        }

    def _gather_speed_data(self) -> dict[str, str]:
        """Gather speed test results."""
        speed = self.query_one(SpeedTestTool)
        return {
            "dl": speed.query_one("#spd_download", InfoBox).value_text,
            "ul": speed.query_one("#spd_upload", InfoBox).value_text,
            "ping": speed.query_one("#spd_ping", InfoBox).value_text,
        }

    def _gather_nmap_data(self) -> list[dict[str, str]]:
        """Gather Nmap scan data."""
        nmap_tool = self.query_one(NmapTool)
        return nmap_tool.scan_data

    def _gather_notes(self) -> str:
        """Gather user notes."""
        return self.query_one("#notes_area", TextArea).text

    def _build_report(
        self,
        timestamp: str,
        dashboard_data: dict[str, str],
        connection_data: dict[str, str],
        speed_data: dict[str, str],
        nmap_data: list[dict[str, str]],
        notes: str,
    ) -> list[str]:
        """Build the report string from gathered data."""
        report = []
        report.append("=" * 50)
        report.append(f"NETWORK TRIAGE REPORT - {timestamp}")
        report.append("=" * 50 + "\n")

        # System info
        report.append("SYSTEM INFO")
        report.append(f"Hostname:    {dashboard_data['hostname']}")
        report.append(f"OS:          {dashboard_data['os_sys']}")
        report.append(f"Internal IP: {dashboard_data['int_ip']}")
        report.append(f"Public IP:   {dashboard_data['pub_ip']}\n")

        # Connection details
        report.append("CONNECTION DETAILS")
        report.append(f"Interface:   {connection_data['iface_name']}")
        report.append(f"Type:        {connection_data['iface_type']}")
        report.append(f"Status:      {connection_data['iface_status']}")
        report.append(f"Speed/MTU:   {connection_data['iface_speed']} / {connection_data['iface_mtu']}")
        report.append(f"DNS:         {connection_data['iface_dns']}")
        if connection_data["wifi_ssid"] != "N/A":
            report.append(f"Wi-Fi:       {connection_data['wifi_ssid']} (Ch: {connection_data['wifi_channel']})")
        report.append("")

        # Speed test
        if speed_data["dl"] != "...":
            report.append("SPEED TEST")
            report.append(f"Download:    {speed_data['dl']}")
            report.append(f"Upload:      {speed_data['ul']}")
            report.append(f"Ping:        {speed_data['ping']}\n")

        # Nmap results
        if nmap_data:
            report.append("NMAP SCAN RESULTS")
            report.append(f"{'IP':<16} {'HOSTNAME':<25} {'STATUS':<10} {'VENDOR'}")
            report.append("-" * 70)
            for host in nmap_data:
                ip = host.get("ip", "N/A")
                name = host.get("hostname", "")[:24]  # Truncate long names
                status = host.get("status", "")
                vendor = host.get("vendor", "")
                report.append(f"{ip:<16} {name:<25} {status:<10} {vendor}")
            report.append("")

        # User notes
        if notes.strip():
            report.append("USER NOTES")
            report.append("-" * 50)
            report.append(notes)
            report.append("-" * 50)

        return report

    def _write_report(self, filename: str, report: list[str]) -> None:
        """Write the report to a file."""
        try:
            with Path(filename).open("w", encoding="utf-8") as f:
                f.write("\n".join(report))
            self.notify(f"Report saved to {filename}", severity="information", timeout=5)
        except (OSError, PermissionError, UnicodeEncodeError) as e:
            self.notify(f"Failed to save: {e}", severity="error")


def run() -> None:
    """Entry point for the console script."""
    import logging

    from .config import settings
    from .logging import configure_logging

    # Map string log level to logging constant
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    configure_logging(level=level, json_format=settings.log_json)

    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-V"):
        try:
            version = importlib.metadata.version("network-triage")
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
        print(f"Network Triage Tool v{version}")
        sys.exit(0)

    app = NetworkTriageApp()
    app.run()


if __name__ == "__main__":
    run()
