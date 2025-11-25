from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Label, Input, Button, Log
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual.reactive import reactive

import sys
import os

# Ensure we can find the src module
sys.path.append(os.getcwd())

from src.macos.network_toolkit import NetworkTriageToolkit

net_tool = NetworkTriageToolkit()

class InfoBox(Static):
    """A custom widget to display a Title and a Value nicely."""
    
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
        if not self.is_mounted:
            return
        self.query_one(".label-title", Label).update(new_val)

    def watch_value_text(self, new_val):
        if not self.is_mounted:
            return
        self.query_one(".label-value", Label).update(new_val)


class Dashboard(Container):
    """The Dashboard Tab Content."""

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


class PingTool(Container):
    """A dedicated tool for Continuous Ping."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="ping_controls"):
            yield Input(placeholder="Enter IP (e.g. 8.8.8.8)", id="ping_input")
            yield Button("Start", id="start_ping_btn", variant="success")
            yield Button("Stop", id="stop_ping_btn", variant="error", disabled=True)
        
        yield Log(id="ping_log", highlight=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start_ping_btn":
            self.action_start_ping()
        elif event.button.id == "stop_ping_btn":
            self.action_stop_ping()

    def action_start_ping(self) -> None:
        host = self.query_one("#ping_input", Input).value
        if not host:
            self.notify("Please enter a valid IP or Hostname", severity="error")
            return

        self.query_one("#start_ping_btn", Button).disabled = True
        self.query_one("#stop_ping_btn", Button).disabled = False
        self.query_one("#ping_input", Input).disabled = True
        
        log = self.query_one("#ping_log", Log)
        log.clear()
        log.write(f"--- Starting Ping to {host} ---\n")

        # Starts the threaded worker automatically
        self.start_ping_worker(host)

    def action_stop_ping(self) -> None:
        net_tool.stop_ping()
        self.workers.cancel_group(self, "ping_job")

        self.query_one("#ping_log", Log).write("\n--- Ping Stopped ---\n")
        
        self.query_one("#start_ping_btn", Button).disabled = False
        self.query_one("#stop_ping_btn", Button).disabled = True
        self.query_one("#ping_input", Input).disabled = False

    @work(thread=True, group="ping_job")
    def start_ping_worker(self, host):
        def write_to_log(line):
            self.app.call_from_thread(self.query_one("#ping_log", Log).write, line)
        net_tool.continuous_ping(host, write_to_log)


class SpeedTestTool(Container):
    """A tool to run Speedtest.net checks."""
    
    def compose(self) -> ComposeResult:
        yield Button("Run Speed Test", id="btn_speed", variant="primary")
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
        self.query_one("#speed_status", Label).update("Initializing Speedtest...")
        
        for widget in self.query(InfoBox):
            widget.value_text = "..."
            
        self.run_speedtest_worker()

    @work(thread=True)
    def run_speedtest_worker(self):
        self.app.call_from_thread(
            self.query_one("#speed_status", Label).update, 
            "Testing Download & Upload (this takes ~20s)..."
        )
        
        results = net_tool.run_speed_test()
        
        self.app.call_from_thread(self.display_results, results)

    def display_results(self, results):
        self.query_one("#btn_speed", Button).disabled = False
        self.query_one("#speed_status", Label).update("Test Complete.")

        # DEBUG: Verify we actually got data by popping a notification
        self.notify(f"DEBUG DATA: {results}", timeout=10)
        
        if "Error" in results:
            self.notify(results["Error"], severity="error")
            self.query_one("#speed_status", Label).update("Failed.")
            return

        self.query_one("#spd_download", InfoBox).value_text = results.get("Download", "N/A")
        self.query_one("#spd_upload", InfoBox).value_text = results.get("Upload", "N/A")
        self.query_one("#spd_ping", InfoBox).value_text = results.get("Ping", "N/A")
        self.query_one("#spd_isp", InfoBox).value_text = results.get("ISP", "N/A")
        self.query_one("#spd_server", InfoBox).value_text = results.get("Server", "N/A")


class NetworkTriageApp(App):
    """A Textual TUI for Network Triage."""

    CSS_PATH = "triage.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "show_tab('dashboard')", "Dashboard"),
        Binding("c", "show_tab('connection')", "Connection"),
        Binding("s", "show_tab('speed')", "Speed Test"),
        Binding("p", "show_tab('ping')", "Ping"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with TabbedContent(initial="dashboard", id="main_tabs"):
            with TabPane("Dashboard", id="dashboard"):
                yield Dashboard()
                
            with TabPane("Connection", id="connection"):
                yield Label("Interface details will go here")
            
            with TabPane("Speed Test", id="speed"):
                yield SpeedTestTool()

            with TabPane("Ping", id="ping"):
                yield PingTool()

        yield Footer()

    def action_show_tab(self, tab: str) -> None:
        self.query_one("#main_tabs").active = tab

if __name__ == "__main__":
    app = NetworkTriageApp()
    app.run()