"""DNS Resolver Widget for Phase 4.2."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, Select, Static

from network_triage.exports import export_to_csv, export_to_json

# Import DNS utilities
from shared.dns_utils import DNSStatus
from shared.dns_utils import resolve_hostname as resolve_dns_hostname

from .base import BaseWidget, TaskCompleted
from .components import HistoryInput, ResultColumn, ResultsWidget

if TYPE_CHECKING:
    from textual.app import ComposeResult


class DNSResolverWidget(BaseWidget):
    """DNS Resolver Widget - resolves hostnames to IP addresses."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.widget_name = "DNSResolverWidget"
        self._last_results: list[dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        # Title
        yield Label("[bold]DNS Resolver[/bold]", id="title")

        # Error display (required by BaseWidget)
        yield Static(id="error-display", classes="error-message")

        # Input section
        with Vertical(id="input-section"):
            # Hostname input
            yield Label("Hostname:")
            yield HistoryInput(id="hostname-input", placeholder="example.com", tooltip="Enter hostname to resolve")

            # Query type select
            yield Label("Query Type:")
            yield Select(
                [
                    ("A Records (IPv4)", "A"),
                    ("AAAA Records (IPv6)", "AAAA"),
                    ("Both (A + AAAA)", "BOTH"),
                    ("Reverse DNS (PTR)", "PTR"),
                    ("All Records", "ALL"),
                ],
                id="query-type-select",
                value="A",
            )

            # DNS server input (optional)
            yield Label("DNS Server (optional):")
            yield Input(
                id="dns-server-input",
                placeholder="Leave blank for system DNS",
                tooltip="Optional: specify custom DNS server",
            )

            # Action buttons
            with Horizontal(id="button-section"):
                yield Button("Resolve", id="resolve-btn", variant="primary")
                yield Button("Export", id="export-btn", variant="success")
                yield Button("Clear", id="clear-btn", variant="default")

        # Results section
        yield Label("[bold]Results[/bold]", id="results-title")

        # Results table
        columns = [
            ResultColumn("Type", "type", width=10),
            ResultColumn("Value", "value", width=40),
            ResultColumn("Time (ms)", "time", width=12),
        ]
        self.results_widget = ResultsWidget(columns=columns)
        yield self.results_widget

        # Status section
        yield Label("", id="status-label")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        match event.button.id:
            case "resolve-btn":
                self.resolve_hostname()
            case "export-btn":
                self.export_results()
            case "clear-btn":
                self.clear_results()

    def resolve_hostname(self) -> None:
        """Resolve the hostname using Phase 3 DNS utilities."""
        try:
            # Get hostname from input
            hostname_input = self.query_one("#hostname-input", HistoryInput)
            hostname = hostname_input.value.strip()

            # Validate input
            if not hostname:
                self.display_error("Please enter a hostname")
                self.set_status("Error: No hostname entered")
                return

            # Push to history
            hostname_input.push_history(hostname)

            # Get query type from select
            query_type_select = self.query_one("#query-type-select", Select)
            query_type = query_type_select.value or "A"

            # Show loading state
            self.show_loading(f"Resolving {hostname}...")
            self.set_status(f"Resolving {hostname}...")

            # Clear previous results
            self.results_widget.clear_results()

            # Perform DNS resolution using Phase 3 utility
            # This is synchronous, so it works in the main thread
            result = resolve_dns_hostname(hostname, timeout=5, include_reverse_dns=True)
            self._last_results = []

            # Check if resolution was successful
            match result.status:
                case DNSStatus.NOT_FOUND:
                    self.display_error(f"Could not resolve {hostname}")
                    self.set_status(f"Failed to resolve {hostname}")
                    return
                case DNSStatus.TIMEOUT:
                    self.display_error("DNS resolution timeout")
                    self.set_status("Timeout - no response from DNS server")
                    return
                case DNSStatus.ERROR:
                    self.display_error(f"Error: {result.error_message}")
                    self.set_status(f"Error: {result.error_message}")
                    return
                case _:
                    pass

            # Display results based on query type
            record_count = 0

            # Add A records (IPv4)
            if query_type in ["A", "BOTH", "ALL"] and result.ipv4_addresses:
                for ip in result.ipv4_addresses:
                    # Find the record with this IP to get timing
                    record = next((r for r in result.records if r.value == ip and r.record_type == "A"), None)
                    self.results_widget.add_result_row(
                        type="A",
                        value=ip,
                        time=f"{record.query_time_ms:.2f}" if record else "N/A",
                    )
                    record_count += 1

            # Add AAAA records (IPv6)
            if query_type in ["AAAA", "BOTH", "ALL"] and result.ipv6_addresses:
                for ip in result.ipv6_addresses:
                    # Find the record with this IP to get timing
                    record = next((r for r in result.records if r.value == ip and r.record_type == "AAAA"), None)
                    self.results_widget.add_result_row(
                        type="AAAA",
                        value=ip,
                        time=f"{record.query_time_ms:.2f}" if record else "N/A",
                    )
                    record_count += 1

            # Add PTR record (Reverse DNS)
            if query_type in ["PTR", "ALL"] and result.reverse_dns:
                record = next((r for r in result.records if r.record_type == "PTR"), None)
                self.results_widget.add_result_row(
                    type="PTR",
                    value=result.reverse_dns,
                    time=f"{record.query_time_ms:.2f}" if record else "N/A",
                )
                record_count += 1

            # Show success message
            if record_count > 0:
                self.display_success(f"Resolved {hostname} - Found {record_count} record(s) in {result.lookup_time_ms:.2f}ms")
                self.set_status(f"✓ Resolved {hostname} - {record_count} records found")
            else:
                self.display_error(f"No records found for {hostname}")
                self.set_status(f"No records found for {hostname}")

            # Notify app that task is complete (for tab badges)
            self.post_message(TaskCompleted(self.id))

        except Exception as e:
            self.display_error(f"Error: {e!s}")
            self.set_status(f"Error: {e!s}")

    def export_results(self) -> None:
        """Export current results to CSV and JSON in the user's home directory."""
        if not self._last_results:
            self.display_error("No results to export")
            return

        try:
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = Path.home() / "NetworkTriageExports"

            json_path = export_dir / f"dns_results_{timestamp}.json"
            csv_path = export_dir / f"dns_results_{timestamp}.csv"

            success_json = export_to_json(self._last_results, json_path)
            success_csv = export_to_csv(self._last_results, csv_path)

            if success_json and success_csv:
                self.display_success(f"Exported to {export_dir}")
                self.notify(f"Results exported to {export_dir}", severity="information")
            else:
                self.display_error("Failed to export some formats")
        except Exception as e:
            self.display_error(f"Export error: {e!s}")

    def clear_results(self) -> None:
        """Clear all results and inputs."""
        try:
            # Clear inputs
            self._last_results = []
            hostname_input = self.query_one("#hostname-input", Input)
            hostname_input.value = ""

            dns_server_input = self.query_one("#dns-server-input", Input)
            dns_server_input.value = ""

            # Clear results
            self.results_widget.clear_results()

            # Clear status
            status_label = self.query_one("#status-label", Label)
            status_label.update("")

            self.set_status("Ready")
            self.display_success("Cleared all results")

        except Exception as e:
            self.display_error(f"Error clearing: {e!s}")
