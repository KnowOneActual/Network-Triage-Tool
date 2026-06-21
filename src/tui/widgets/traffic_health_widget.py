"""Traffic Health Widget for Phase 5.

Provides passive packet monitoring statistics, traffic type distribution,
and historical comparison.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from textual import work
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from network_triage.exports import export_to_csv, export_to_json
from network_triage.shared.traffic_health import TrafficHealthMonitor

from .base import BaseWidget, TaskCompleted

if TYPE_CHECKING:
    from textual.app import ComposeResult


class TrafficHealthWidget(BaseWidget):
    """Traffic Health Analyzer widget providing passive broadcast & unicast monitoring."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.widget_name = "TrafficHealthWidget"
        self.monitor = TrafficHealthMonitor()
        self._last_stats: dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        # Title
        yield Label("[bold]Traffic Health Analyzer[/bold]", id="title")

        # Error display (required by BaseWidget)
        yield Static(id="error-display", classes="error-message")

        # Status mode / simulation warning
        yield Static("", id="mode-status")

        # Control panel
        with Horizontal(id="control-section", classes="tool_header"):
            yield Button("Start Monitor", id="traffic-start-btn", variant="success")
            yield Button("Stop", id="traffic-stop-btn", variant="error", disabled=True)
            yield Button("Save to History", id="traffic-save-btn", variant="primary", disabled=True)
            yield Button("Export", id="traffic-export-btn", variant="default")
            yield Button("Clear", id="traffic-clear-btn", variant="default")

        # Statistics display split
        with Horizontal(id="stats-split"):
            # Traffic type distribution (unicast/multicast/broadcast)
            with Vertical(id="dist-panel", classes="stats-panel"):
                yield Label("[bold]Traffic Type Distribution[/bold]", classes="panel-title")
                yield Static("Start monitoring to analyze traffic distribution.", id="dist-details")

            # Protocol counters
            with Vertical(id="proto-panel", classes="stats-panel"):
                yield Label("[bold]Broadcast & Multicast Protocols[/bold]", classes="panel-title")
                yield Static("Start monitoring to count broadcast protocols.", id="proto-details")

        # Historical Comparison Section
        yield Label("[bold]Historical Comparison (Yesterday vs. Today)[/bold]", id="history-title")
        yield Static("No historical data compared yet. Save current session to compile history.", id="history-comparison")

        # History table
        yield Label("[bold]Saved Capture History[/bold]", id="history-table-title")
        yield DataTable(id="history-table")

        # Status label
        yield Label("Ready", id="status-label")

    def on_mount(self) -> None:
        """Initialize table columns and check comparison on startup."""
        table = self.query_one("#history-table", DataTable)
        table.add_columns("Date/Time", "Total Pkts", "PPS", "Unicast %", "Multicast %", "Broadcast %")
        table.cursor_type = "row"
        self.update_history_table()
        self.update_comparison()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button controls."""
        match event.button.id:
            case "traffic-start-btn":
                self.start_monitoring()
            case "traffic-stop-btn":
                self.stop_monitoring()
            case "traffic-save-btn":
                self.save_session()
            case "traffic-export-btn":
                self.export_results()
            case "traffic-clear-btn":
                self.clear_stats()

    def start_monitoring(self) -> None:
        """Start the passive packet capture in a background thread."""
        self.show_loading("Monitoring network traffic...")
        self.set_status("Monitoring...")
        self.query_one("#traffic-start-btn", Button).disabled = True
        self.query_one("#traffic-stop-btn", Button).disabled = False
        self.query_one("#traffic-save-btn", Button).disabled = True

        # Start sniffing
        self.monitor.start(callback=self.on_packet_received)

    @work(thread=True)
    def stop_monitoring(self) -> None:
        """Stop passive monitoring and update controls."""
        self.monitor.stop()
        self.app.call_from_thread(self.finished_monitoring)

    def finished_monitoring(self) -> None:
        """Thread-safe UI updates when monitoring is stopped."""
        self.is_loading = False
        self.set_status("Monitoring Stopped")
        self.query_one("#traffic-start-btn", Button).disabled = False
        self.query_one("#traffic-stop-btn", Button).disabled = True
        self.query_one("#traffic-save-btn", Button).disabled = False
        self.post_message(TaskCompleted(self.id))

    def on_packet_received(self, monitor: TrafficHealthMonitor) -> None:
        """Callback invoked from sniffing thread on packet updates."""
        stats = monitor.get_stats()
        self._last_stats = stats
        self.app.call_from_thread(self.update_ui_stats, stats)

    def update_ui_stats(self, stats: dict[str, Any]) -> None:
        """Updates the text and visual meters on packet updates."""
        # Simulation warning update
        mode_label = self.query_one("#mode-status", Static)
        if stats["is_simulated"]:
            mode_label.update(
                "[bold yellow]⚠️ Running in Simulation Mode (Requires sudo / root for live raw packet capture)[/bold yellow]"
            )
        else:
            mode_label.update("[bold green]✔ Live Network Packet Capture Active[/bold green]")

        # Total count info
        total = stats["total_packets"]
        pps = stats["packets_per_second"]
        elapsed = stats["elapsed_seconds"]

        # Calculate percentages safely
        uni_pct = (stats["unicast_packets"] / total * 100) if total > 0 else 0.0
        multi_pct = (stats["multicast_packets"] / total * 100) if total > 0 else 0.0
        broad_pct = (stats["broadcast_packets"] / total * 100) if total > 0 else 0.0

        def _make_meter(pct: float) -> str:
            filled = round(pct / 5)
            return f"[{'█' * filled}{'░' * (20 - filled)}] {pct:.1f}%"

        dist_text = (
            f"Total Packets: [bold]{total}[/bold] | Rate: [bold]{pps} pps[/bold] | Duration: {int(elapsed)}s\n\n"
            f"[bold]Unicast:[/bold] {stats['unicast_packets']} packets\n"
            f"{_make_meter(uni_pct)}\n\n"
            f"[bold]Multicast:[/bold] {stats['multicast_packets']} packets\n"
            f"{_make_meter(multi_pct)}\n\n"
            f"[bold]Broadcast:[/bold] {stats['broadcast_packets']} packets\n"
            f"{_make_meter(broad_pct)}"
        )
        self.query_one("#dist-details", Static).update(dist_text)

        # Protocol Details (DHCP, ARP, STP, LLDP, CDP)
        arp_pct = (stats["arp_packets"] / total * 100) if total > 0 else 0.0
        dhcp_pct = (stats["dhcp_packets"] / total * 100) if total > 0 else 0.0
        stp_pct = (stats["stp_packets"] / total * 100) if total > 0 else 0.0
        lldp_pct = (stats["lldp_packets"] / total * 100) if total > 0 else 0.0
        cdp_pct = (stats["cdp_packets"] / total * 100) if total > 0 else 0.0

        proto_text = (
            f"[bold]ARP:[/bold] {stats['arp_packets']} ({arp_pct:.1f}%)\n"
            f"[bold]DHCP/BOOTP:[/bold] {stats['dhcp_packets']} ({dhcp_pct:.1f}%)\n"
            f"[bold]STP:[/bold] {stats['stp_packets']} ({stp_pct:.1f}%)\n"
            f"[bold]LLDP:[/bold] {stats['lldp_packets']} ({lldp_pct:.1f}%)\n"
            f"[bold]CDP:[/bold] {stats['cdp_packets']} ({cdp_pct:.1f}%)\n\n"
            f"[bold]General Transport Protocols:[/bold]\n"
            f"IPv4: {stats['ipv4_packets']} | IPv6: {stats['ipv6_packets']}\n"
            f"TCP: {stats['tcp_packets']} | UDP: {stats['udp_packets']}\n"
            f"ICMP: {stats['icmp_packets']} | DNS: {stats['dns_packets']}"
        )
        self.query_one("#proto-details", Static).update(proto_text)

    def save_session(self) -> None:
        """Save the current stats to history."""
        if not self._last_stats:
            self.display_error("No stats recorded to save.")
            return

        self.monitor.save_to_history()
        self.display_success("Capture saved to history.")
        self.update_history_table()
        self.update_comparison()
        self.query_one("#traffic-save-btn", Button).disabled = True

    def update_history_table(self) -> None:
        """Repopulates the history DataTable."""
        table = self.query_one("#history-table", DataTable)
        table.clear()

        history = self.monitor.load_history()
        for entry in reversed(history):
            try:
                dt = datetime.fromisoformat(entry["timestamp"]).strftime("%m/%d %H:%M")
                tot = entry["total_packets"]
                uni = (entry["unicast_packets"] / tot * 100) if tot > 0 else 0.0
                multi = (entry["multicast_packets"] / tot * 100) if tot > 0 else 0.0
                broad = (entry["broadcast_packets"] / tot * 100) if tot > 0 else 0.0

                table.add_row(
                    dt,
                    str(tot),
                    f"{entry['packets_per_second']} pps",
                    f"{uni:.1f}%",
                    f"{multi:.1f}%",
                    f"{broad:.1f}%",
                )
            except KeyError, ValueError:
                continue

    def update_comparison(self) -> None:
        """Finds yesterday's record and compares stats."""
        yesterday = self.monitor.get_yesterday_comparison()
        comparison_label = self.query_one("#history-comparison", Static)

        if not yesterday:
            comparison_label.update(
                "No baseline historical record found from yesterday for comparison. Save a capture to build history."
            )
            return

        try:
            prev_tot = yesterday["total_packets"]
            prev_pps = yesterday["packets_per_second"]
            prev_broad = (yesterday["broadcast_packets"] / prev_tot * 100) if prev_tot > 0 else 0.0

            dt_str = datetime.fromisoformat(yesterday["timestamp"]).strftime("%Y-%m-%d %H:%M")

            comparison_text = (
                f"Comparing with baseline capture from [cyan]{dt_str}[/cyan]:\n• Packet Rate: [bold]{prev_pps} pps[/bold] vs. "
            )

            if self._last_stats:
                curr_pps = self._last_stats["packets_per_second"]
                curr_tot = self._last_stats["total_packets"]
                curr_broad = (self._last_stats["broadcast_packets"] / curr_tot * 100) if curr_tot > 0 else 0.0

                pps_delta = curr_pps - prev_pps
                broad_delta = curr_broad - prev_broad

                pps_trend = "▲" if pps_delta > 0 else "▼"
                broad_trend = "▲" if broad_delta > 0 else "▼"

                comparison_text += (
                    f"[bold]{curr_pps} pps[/bold] ({pps_trend} {abs(pps_delta):.1f})\n"
                    f"• Broadcast Ratio: [bold]{prev_broad:.1f}%[/bold] vs. [bold]{curr_broad:.1f}%[/bold] "
                    f"({broad_trend} {abs(broad_delta):.1f}%)"
                )
            else:
                comparison_text += "Pending new monitor run..."

            comparison_label.update(comparison_text)
        except Exception as e:
            comparison_label.update(f"Error parsing historical comparison: {e}")

    def clear_stats(self) -> None:
        """Clear the current stats panels."""
        self.monitor.reset()
        self._last_stats = {}
        self.query_one("#dist-details", Static).update("Start monitoring to analyze traffic distribution.")
        self.query_one("#proto-details", Static).update("Start monitoring to count broadcast protocols.")
        self.query_one("#traffic-save-btn", Button).disabled = True
        self.update_comparison()
        self.set_status("Ready")

    def export_results(self) -> None:
        """Export current session or history to JSON/CSV."""
        if not self._last_stats:
            self.display_error("No current monitor run stats available to export.")
            return

        export_dir = Path.home() / "Downloads"
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            export_dir = Path.cwd()

        json_path = export_dir / f"traffic_health_capture_{int(self._last_stats['elapsed_seconds'])}s.json"
        csv_path = export_dir / f"traffic_health_capture_{int(self._last_stats['elapsed_seconds'])}s.csv"

        # Save JSON
        success_json = export_to_json(self._last_stats, json_path)

        # Save CSV (needs list format)
        success_csv = export_to_csv([self._last_stats], csv_path)

        if success_json or success_csv:
            self.display_success(f"Exported traffic stats to {export_dir}")
        else:
            self.display_error("Failed to export files.")
