"""Port Scanner Widget for Phase 4.3."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING, Any

from textual import work
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, Select, Static

from shared.port_utils import (
    COMMON_SERVICE_PORTS,
    PortCheckResult,
    PortStatus,
    check_multiple_ports,
    summarize_port_scan,
)

from .base import BaseWidget
from .components import ResultColumn, ResultsWidget

if TYPE_CHECKING:
    from textual.app import ComposeResult

logger = logging.getLogger(__name__)


class PortScannerWidget(BaseWidget):
    """Port Scanner Widget - scans and detects open ports."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.widget_name = "PortScannerWidget"
        self.scan_in_progress = False

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        # Title
        yield Label("[bold]Port Scanner[/bold]", id="title")

        # Error display (required by BaseWidget)
        yield Static(id="error-display", classes="error-message")

        # Input section
        with Vertical(id="input-section"):
            # Host input
            yield Label("Target Host:")
            yield Input(id="host-input", placeholder="localhost or 192.168.1.1", tooltip="Enter hostname or IP address")

            # Scan mode select
            yield Label("Scan Mode:")
            yield Select(
                [
                    ("Common Services (30 ports)", "common"),
                    ("Single Port", "single"),
                    ("Multiple Ports (comma-separated)", "multiple"),
                    ("Port Range (e.g. 1-1024)", "range"),
                ],
                id="scan-mode-select",
                value="common",
            )

            # Port input (conditional based on mode)
            yield Label("Ports (for single/multiple/range):")
            yield Input(
                id="port-input",
                placeholder="e.g. 80 or 80,443,22 or 1-1024",
                tooltip="Port number, comma-separated ports, or port range",
            )

            # Timeout setting
            yield Label("Timeout per port (seconds):")
            yield Input(id="timeout-input", value="3", placeholder="3", tooltip="Connection timeout in seconds")

            # Action buttons
            with Horizontal(id="button-section"):
                yield Button("Scan", id="scan-btn", variant="primary")
                yield Button("Clear", id="clear-btn", variant="default")

        # Results section
        yield Label("[bold]Results[/bold]", id="results-title")

        # Results table
        columns = [
            ResultColumn("Port", "port", width=8),
            ResultColumn("Service", "service", width=20),
            ResultColumn("Status", "status", width=12),
            ResultColumn("Time (ms)", "time", width=12),
        ]
        self.results_widget = ResultsWidget(columns=columns)
        yield self.results_widget

        # Summary section
        yield Label("", id="summary-label")

        # Status section
        yield Label("", id="status-label")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "scan-btn":
            self.scan_ports()
        elif event.button.id == "clear-btn":
            self.clear_results()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle scan mode changes."""
        # Update UI based on selected scan mode
        # This could be enhanced to show/hide port input based on mode

    def parse_ports_input(self, port_input: str, mode: str) -> list[int] | None:
        """Parse port input based on scan mode."""
        port_input = port_input.strip()

        match mode:
            case "single":
                try:
                    port = int(port_input)
                    if 1 <= port <= 65535:
                        return [port]
                    logger.warning(f"Port {port} out of range (1-65535)")
                    return None
                except ValueError:
                    logger.warning(f"Invalid port number: {port_input}")
                    return None

            case "multiple":
                try:
                    if not port_input:
                        logger.warning("Empty port input")
                        return None

                    ports = []
                    for port_str in port_input.split(","):
                        port_str = port_str.strip()
                        if not port_str:
                            continue
                        port = int(port_str)
                        if 1 <= port <= 65535:
                            ports.append(port)
                        else:
                            logger.warning(f"Port {port} out of range (1-65535)")
                            return None

                    if not ports:
                        logger.warning("No valid ports provided")
                        return None

                    return sorted(set(ports))  # Remove duplicates and sort
                except ValueError as e:
                    logger.warning(f"Invalid port format: {port_input} - {e}")
                    return None

            case "range":
                # Parse range like "1-1024"
                if not port_input:
                    logger.warning("Empty range input")
                    return None

                regex_match = re.match(r"^(\d+)\s*-\s*(\d+)$", port_input)
                if not regex_match:
                    logger.warning(f"Invalid range format: {port_input}")
                    return None

                try:
                    start = int(regex_match.group(1))
                    end = int(regex_match.group(2))

                    if not (1 <= start <= 65535 and 1 <= end <= 65535):
                        logger.warning(f"Range ports out of bounds: {start}-{end}")
                        return None

                    if start > end:
                        start, end = end, start

                    # Limit range to prevent excessive scanning
                    port_count = end - start + 1
                    if port_count > 5000:
                        logger.warning(f"Range too large: {port_count} ports (max 5000)")
                        return None

                    return list(range(start, end + 1))
                except ValueError as e:
                    logger.warning(f"Error parsing range: {e}")
                    return None

            case _:
                logger.warning(f"Unknown mode: {mode}")
                return None

    def scan_ports(self) -> None:
        """Scan the target host ports using Phase 3 port utilities."""
        if self.scan_in_progress:
            self.display_error("Scan already in progress")
            return

        try:
            # Get inputs
            host_input = self.query_one("#host-input", Input)
            host = host_input.value.strip()

            # Validate host
            if not host:
                self.display_error("Please enter a target host")
                self.set_status("Error: No host specified")
                return

            # Get scan mode
            scan_mode_select = self.query_one("#scan-mode-select", Select)
            scan_mode = scan_mode_select.value if isinstance(scan_mode_select.value, str) else "common"

            # Get timeout
            timeout_input = self.query_one("#timeout-input", Input)
            try:
                timeout = int(timeout_input.value.strip())
                if timeout < 1 or timeout > 30:
                    self.display_error("Timeout must be between 1 and 30 seconds")
                    return
            except ValueError:
                self.display_error("Invalid timeout value")
                return

            # Clear previous results
            self.results_widget.clear_results()
            summary_label = self.query_one("#summary-label", Label)
            summary_label.update("")

            # Parse ports based on mode
            ports_to_scan: list[int] = []

            if scan_mode == "common":
                ports_to_scan = list(COMMON_SERVICE_PORTS.keys())
                port_description = f"common services ({len(ports_to_scan)} ports)"
            else:
                # Parse port input for other modes
                port_input = self.query_one("#port-input", Input)
                port_str = port_input.value.strip()

                if not port_str:
                    self.display_error(f"Please specify ports for {scan_mode} scan")
                    return

                parsed_ports = self.parse_ports_input(port_str, scan_mode)
                if parsed_ports is None:
                    # Provide specific error message based on mode
                    if scan_mode == "single":
                        self.display_error("Invalid port number (must be 1-65535)")
                    elif scan_mode == "multiple":
                        self.display_error("Invalid ports: use comma-separated numbers (1-65535)")
                    elif scan_mode == "range":
                        self.display_error("Invalid range: use format 'start-end' (e.g. 1-1024)")
                    return

                ports_to_scan = parsed_ports
                port_description = f"{len(ports_to_scan)} port(s)"

            # Show loading state
            self.show_loading(f"Scanning {host} ({port_description})...")
            self.set_status(f"Scanning {host}...")
            self.scan_in_progress = True

            # Start background worker
            self._run_scan_worker(host, ports_to_scan, timeout)

        except Exception as e:
            self.display_error(f"Scan error: {e!s}")
            self.set_status(f"Error: {e!s}")
            self.scan_in_progress = False

    @work(group="scan_job")
    async def _run_scan_worker(self, host: str, ports: list[int], timeout_secs: int) -> None:
        """Run the port scan in the background."""
        try:
            async with asyncio.timeout(timeout_secs * 2 + 10):  # Safety timeout
                results = await check_multiple_ports(host, ports, timeout_secs=timeout_secs, max_workers=10)
                self._display_results(results, host)
        except TimeoutError:
            self.display_error(f"Scan timed out for {host}")
        except Exception as e:
            logger.error(f"Port scan worker error: {e}", exc_info=True)
            self.display_error(f"Scan failed: {e}")
        finally:
            self.scan_in_progress = False

    def _display_results(self, results: list[PortCheckResult], host: str) -> None:
        """Display scan results (UI thread)."""
        summary_label = self.query_one("#summary-label", Label)

        # Display results
        if results:
            for result in results:
                # Determine status color
                status_str = result.status.value.upper()
                match result.status:
                    case PortStatus.OPEN:
                        status_str = f"[green]{status_str}[/green]"
                    case PortStatus.CLOSED:
                        status_str = f"[red]{status_str}[/red]"
                    case PortStatus.FILTERED:
                        status_str = f"[yellow]{status_str}[/yellow]"
                    case _:
                        status_str = f"[dim]{status_str}[/dim]"

                self.results_widget.add_result_row(
                    port=str(result.port),
                    service=result.service_name or "Unknown",
                    status=status_str,
                    time=f"{result.response_time_ms:.1f}",
                )

            # Generate and display summary
            summary = summarize_port_scan(results)
            summary_text = (
                f"Total: {summary['total_scanned']} | "
                f"[green]Open: {summary['open_count']}[/green] | "
                f"[red]Closed: {summary['closed_count']}[/red] | "
                f"[yellow]Filtered: {summary['filtered_count']}[/yellow] | "
                f"Avg Time: {summary['avg_response_time_ms']:.1f}ms"
            )
            summary_label.update(summary_text)

            # Show success message
            if summary["open_count"] > 0:
                self.display_success(f"Scan complete! Found {summary['open_count']} open port(s) on {host}")
            else:
                self.display_success(f"Scan complete on {host}. No open ports found.")

            self.set_status(
                f"✓ Scanned {host} - {summary['open_count']} open, "
                f"{summary['closed_count']} closed, "
                f"{summary['filtered_count']} filtered",
            )
        else:
            self.display_error("No results from scan")
            self.set_status("Scan failed")

    def clear_results(self) -> None:
        """Clear all results and inputs."""
        try:
            # Clear inputs
            host_input = self.query_one("#host-input", Input)
            host_input.value = ""

            port_input = self.query_one("#port-input", Input)
            port_input.value = ""

            # Clear results and summary
            self.results_widget.clear_results()
            summary_label = self.query_one("#summary-label", Label)
            summary_label.update("")

            # Clear status
            status_label = self.query_one("#status-label", Label)
            status_label.update("")

            self.set_status("Ready")
            self.display_success("Cleared all results")

        except Exception as e:
            self.display_error(f"Error clearing: {e!s}")
