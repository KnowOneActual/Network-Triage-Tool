"""Port Scanner Widget for Phase 4.3."""

from .base import BaseWidget
from .components import ResultsWidget, ResultColumn
from textual.app import ComposeResult
from textual.widgets import Input, Button, Label, Select
from textual.containers import Horizontal, Vertical
from typing import List, Optional
import re

# Import port utilities - use relative import from shared module
try:
    from ..shared.port_utils import (
        check_port_open,
        check_multiple_ports,
        scan_common_ports,
        PortStatus,
        COMMON_SERVICE_PORTS,
        summarize_port_scan,
    )
except ImportError:
    # Fallback for different import contexts
    from shared.port_utils import (
        check_port_open,
        check_multiple_ports,
        scan_common_ports,
        PortStatus,
        COMMON_SERVICE_PORTS,
        summarize_port_scan,
    )


class PortScannerWidget(BaseWidget):
    """Port Scanner Widget - scans and detects open ports."""
    
    def __init__(self):
        super().__init__(name="PortScannerWidget")
        self.scan_in_progress = False
    
    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        # Title
        yield Label("[bold]Port Scanner[/bold]", id="title")
        
        # Input section
        with Vertical(id="input-section"):
            # Host input
            yield Label("Target Host:")
            yield Input(
                id="host-input",
                placeholder="localhost or 192.168.1.1",
                tooltip="Enter hostname or IP address"
            )
            
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
                value="common"
            )
            
            # Port input (conditional based on mode)
            yield Label("Ports (for single/multiple/range):")
            yield Input(
                id="port-input",
                placeholder="e.g. 80 or 80,443,22 or 1-1024",
                tooltip="Port number, comma-separated ports, or port range"
            )
            
            # Timeout setting
            yield Label("Timeout per port (seconds):")
            yield Input(
                id="timeout-input",
                value="3",
                placeholder="3",
                tooltip="Connection timeout in seconds"
            )
            
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
        pass
    
    def parse_ports_input(self, port_input: str, mode: str) -> Optional[List[int]]:
        """
        Parse port input based on scan mode.
        
        Args:
            port_input: Raw port input string
            mode: Scan mode (single, multiple, range)
        
        Returns:
            List of port numbers or None if invalid
        """
        port_input = port_input.strip()
        
        if mode == "single":
            try:
                port = int(port_input)
                if 1 <= port <= 65535:
                    return [port]
                else:
                    self.display_error(f"Port must be between 1 and 65535")
                    return None
            except ValueError:
                self.display_error(f"Invalid port number: {port_input}")
                return None
        
        elif mode == "multiple":
            try:
                ports = []
                for port_str in port_input.split(","):
                    port = int(port_str.strip())
                    if 1 <= port <= 65535:
                        ports.append(port)
                    else:
                        self.display_error(f"Port {port} is invalid (must be 1-65535)")
                        return None
                if not ports:
                    self.display_error("No valid ports provided")
                    return None
                return sorted(list(set(ports)))  # Remove duplicates and sort
            except ValueError:
                self.display_error(f"Invalid port format: {port_input}")
                return None
        
        elif mode == "range":
            # Parse range like "1-1024"
            match = re.match(r"^(\d+)\s*-\s*(\d+)$", port_input)
            if not match:
                self.display_error("Invalid range format. Use: start-end (e.g. 1-1024)")
                return None
            
            try:
                start = int(match.group(1))
                end = int(match.group(2))
                
                if not (1 <= start <= 65535 and 1 <= end <= 65535):
                    self.display_error("Ports must be between 1 and 65535")
                    return None
                
                if start > end:
                    start, end = end, start
                
                # Limit range to prevent excessive scanning
                port_count = end - start + 1
                if port_count > 5000:
                    self.display_error(f"Range too large ({port_count} ports). Max 5000.")
                    return None
                
                return list(range(start, end + 1))
            except ValueError:
                self.display_error("Invalid port range")
                return None
        
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
            scan_mode = scan_mode_select.value or "common"
            
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
            ports_to_scan: List[int] = []
            
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
                    return
                
                ports_to_scan = parsed_ports
                port_description = f"{len(ports_to_scan)} port(s)"
            
            # Show loading state
            self.show_loading(f"Scanning {host} ({port_description})...")
            self.set_status(f"Scanning {host}...")
            self.scan_in_progress = True
            
            # Perform port scan using Phase 3 utility
            results = check_multiple_ports(
                host,
                ports_to_scan,
                timeout=timeout,
                max_workers=10
            )
            
            # Display results
            if results:
                for result in results:
                    # Determine status color
                    status_str = result.status.value
                    if result.status == PortStatus.OPEN:
                        status_str = f"[green]{status_str}[/green]"
                    elif result.status == PortStatus.CLOSED:
                        status_str = f"[red]{status_str}[/red]"
                    elif result.status == PortStatus.FILTERED:
                        status_str = f"[yellow]{status_str}[/yellow]"
                    else:
                        status_str = f"[dim]{status_str}[/dim]"
                    
                    self.results_widget.add_row(
                        port=str(result.port),
                        service=result.service_name or "Unknown",
                        status=status_str,
                        time=f"{result.response_time_ms:.1f}"
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
                if summary['open_count'] > 0:
                    self.display_success(
                        f"Scan complete! Found {summary['open_count']} open port(s) "
                        f"on {host}"
                    )
                else:
                    self.display_success(f"Scan complete on {host}. No open ports found.")
                
                self.set_status(
                    f"✓ Scanned {host} - {summary['open_count']} open, "
                    f"{summary['closed_count']} closed, "
                    f"{summary['filtered_count']} filtered"
                )
            else:
                self.display_error(f"No results from scan")
                self.set_status("Scan failed")
            
            self.scan_in_progress = False
        
        except Exception as e:
            self.display_error(f"Scan error: {str(e)}")
            self.set_status(f"Error: {str(e)}")
            self.scan_in_progress = False
    
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
            self.display_error(f"Error clearing: {str(e)}")
