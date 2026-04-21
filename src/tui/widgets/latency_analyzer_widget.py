"""Latency Analyzer Widget for Phase 4.4.

Provides an MTR-style path analyzer showing per-hop latency and packet loss,
plus aggregate ping statistics for the target host.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from textual import work
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Label, Static

from .base import BaseWidget

if TYPE_CHECKING:
    from textual.app import ComposeResult

logger = logging.getLogger(__name__)

# Import latency utilities - Phase 3
from shared.latency_utils import (  # type: ignore[import-untyped]
    PingStatistics,
    TracerouteHop,
    mtr_style_trace,
    ping_statistics,
)


class LatencyAnalyzerWidget(BaseWidget):
    """Latency Analyzer Widget — MTR-style path analysis with per-hop RTT and loss.

    Combines a traceroute path trace with ping statistics to give a complete
    picture of latency across every hop to the target host.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.widget_name = "LatencyAnalyzerWidget"
        self.trace_in_progress = False

    def compose(self) -> ComposeResult:
        """Compose the Latency Analyzer UI."""
        yield Label("[bold]Latency Analyzer[/bold]", id="title")

        # Error display (required by BaseWidget)
        yield Static(id="error-display", classes="error-message")

        # Input section
        with Vertical(id="input-section"):
            yield Label("Target Host:")
            yield Input(
                id="host-input",
                placeholder="e.g. 8.8.8.8 or google.com",
                tooltip="Enter a hostname or IP address to trace",
            )

            with Horizontal(id="button-section"):
                yield Button("▶ Run Analysis", id="run-btn", variant="primary")
                yield Button("Clear", id="clear-btn", variant="default")

        # Hop results table
        yield Label("[bold]Path Analysis (Per-Hop)[/bold]", id="hops-title")
        yield DataTable(id="hops-table")

        # Ping statistics summary
        yield Label("", id="ping-summary-label")

        # Status / error display area (used by BaseWidget.display_error)
        yield Label("", id="status-label")

    def on_mount(self) -> None:
        """Set up the DataTable columns after mount."""
        table = self.query_one("#hops-table", DataTable)
        table.add_columns("Hop", "IP Address", "Hostname", "Avg RTT", "Loss %")
        table.cursor_type = "row"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Run and Clear button presses."""
        match event.button.id:
            case "run-btn":
                self.run_analysis()
            case "clear-btn":
                self.clear_results()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Run analysis when Enter is pressed in the host field."""
        self.run_analysis()

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def run_analysis(self) -> None:
        """Validate host and kick off the background trace + ping."""
        if self.trace_in_progress:
            self.display_error("Analysis already in progress")
            return

        host_input = self.query_one("#host-input", Input)
        host = host_input.value.strip()

        valid, msg = self.validate_host(host)
        if not valid:
            self.display_error(msg)
            self.set_status(f"Error: {msg}")
            return

        # Clear previous results
        self.query_one("#hops-table", DataTable).clear()
        self.query_one("#ping-summary-label", Label).update("")
        self.query_one("#status-label", Label).update("")

        self.show_loading(f"Tracing path to {host}…  (this may take ~30s)")
        self.set_status(f"Running path analysis to {host}…")
        self.trace_in_progress = True

        self._run_trace_worker(host)

    def clear_results(self) -> None:
        """Clear all results, inputs, and status messages."""
        try:
            self.query_one("#host-input", Input).value = ""
            self.query_one("#hops-table", DataTable).clear()
            self.query_one("#ping-summary-label", Label).update("")
            self.query_one("#status-label", Label).update("")
            self.set_status("Ready")
            self.display_success("Cleared all results")
        except Exception as e:
            self.display_error(f"Error clearing: {e!s}")

    # ------------------------------------------------------------------
    # Pure helpers (no app/widget context needed — easy to test)
    # ------------------------------------------------------------------

    @staticmethod
    def validate_host(host: str) -> tuple[bool, str]:
        """Validate a host string.

        Args:
            host: Raw host string from the input field.

        Returns:
            Tuple of (is_valid, error_message). error_message is empty when valid.

        """
        host = host.strip()
        if not host:
            return False, "Please enter a target host"
        if len(host) > 253:
            return False, "Host name is too long (max 253 characters)"
        # Basic sanity: no spaces in the middle
        if " " in host:
            return False, "Host name cannot contain spaces"
        return True, ""

    @staticmethod
    def format_rtt(ms: float | None) -> str:
        """Format an RTT value for display.

        Args:
            ms: RTT in milliseconds, or None for timeout.

        Returns:
            Human-readable string, e.g. "12.3 ms" or "***" for timeout.

        """
        if ms is None:
            return "***"
        return f"{ms:.1f} ms"

    @staticmethod
    def color_rtt(ms: float | None) -> str:
        """Return a Rich-markup coloured RTT string based on latency thresholds.

        Thresholds:
            <50 ms  → green
            <150 ms → yellow
            ≥150 ms → red
            None    → dim (timeout)

        Args:
            ms: RTT in milliseconds, or None for timeout.

        Returns:
            Rich markup string with colour applied.

        """
        if ms is None:
            return "[dim]***[/dim]"
        formatted = f"{ms:.1f} ms"
        if ms < 50:
            return f"[green]{formatted}[/green]"
        if ms < 150:
            return f"[yellow]{formatted}[/yellow]"
        return f"[red]{formatted}[/red]"

    # ------------------------------------------------------------------
    # Background worker
    # ------------------------------------------------------------------

    @work(thread=True)
    def _run_trace_worker(self, host: str) -> None:
        """Run mtr_style_trace + ping_statistics on a background thread."""
        try:
            hops, trace_msg = mtr_style_trace(host, max_hops=30, timeout=3)
            ping_stats = ping_statistics(host, count=5, timeout=3)
            logger.debug(f"Trace complete for {host}: {len(hops)} hops — {trace_msg}")
            self.app.call_from_thread(self._display_results, hops, ping_stats)
        except Exception as e:
            logger.error(f"Trace worker error for {host}: {e}", exc_info=True)
            self.app.call_from_thread(self._on_trace_error, str(e))

    def _display_results(self, hops: list[TracerouteHop], ping_stats: PingStatistics) -> None:
        """Populate the DataTable and summary label with trace results (UI thread)."""
        self.trace_in_progress = False
        table = self.query_one("#hops-table", DataTable)
        table.clear()

        if not hops:
            self.display_error("No hops returned — host may be unreachable or traceroute unavailable")
            self.set_status("No results")
            return

        for hop in hops:
            avg_rtt = hop.avg_rtt_ms()
            table.add_row(
                str(hop.hop_number),
                hop.ip_address or "N/A",
                hop.hostname or "",
                self.color_rtt(avg_rtt),
                "[dim]—[/dim]" if hop.status == "timeout" else "0%",
            )

        # Ping summary
        if ping_stats.status.value == "success" or ping_stats.packets_received > 0:
            loss = ping_stats.packet_loss_percent
            loss_color = "green" if loss == 0 else ("yellow" if loss < 20 else "red")
            summary = (
                f"[bold]Ping Stats:[/bold]  "
                f"Avg [cyan]{self.format_rtt(ping_stats.avg_ms)}[/cyan]  │  "
                f"Min [green]{self.format_rtt(ping_stats.min_ms)}[/green]  │  "
                f"Max [red]{self.format_rtt(ping_stats.max_ms)}[/red]  │  "
                f"Jitter [yellow]{self.format_rtt(ping_stats.stddev_ms)}[/yellow]  │  "
                f"Loss [{loss_color}]{loss:.1f}%[/{loss_color}]"
            )
        else:
            summary = "[red]Ping failed — host may be blocking ICMP[/red]"

        self.query_one("#ping-summary-label", Label).update(summary)
        self.display_success(f"Analysis complete: {len(hops)} hops traced to {ping_stats.host}")
        self.set_status(f"✓ {len(hops)} hops traced")

    def _on_trace_error(self, error_msg: str) -> None:
        """Handle worker errors on the UI thread."""
        self.trace_in_progress = False
        self.display_error(f"Trace failed: {error_msg}")
        self.set_status("Error")
