"""DNS Resolver Widget for Phase 4.2."""

from .base import BaseWidget
from .components import ResultsWidget, ResultColumn
from textual.app import ComposeResult
from textual.widgets import Input, Button, Label, Select
from textual.containers import Horizontal, Vertical

# Import DNS utilities - use relative import from shared module
try:
    from ..shared.dns_utils import resolve_hostname as resolve_dns_hostname, DNSStatus
except ImportError:
    # Fallback for different import contexts
    from shared.dns_utils import resolve_hostname as resolve_dns_hostname, DNSStatus


class DNSResolverWidget(BaseWidget):
    """DNS Resolver Widget - resolves hostnames to IP addresses."""
    
    def __init__(self):
        super().__init__(name="DNSResolverWidget")
    
    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        # Title
        yield Label("[bold]DNS Resolver[/bold]", id="title")
        
        # Input section
        with Vertical(id="input-section"):
            # Hostname input
            yield Label("Hostname:")
            yield Input(
                id="hostname-input",
                placeholder="example.com",
                tooltip="Enter hostname to resolve"
            )
            
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
                value="A"
            )
            
            # DNS server input (optional)
            yield Label("DNS Server (optional):")
            yield Input(
                id="dns-server-input",
                placeholder="Leave blank for system DNS",
                tooltip="Optional: specify custom DNS server"
            )
            
            # Action buttons
            with Horizontal(id="button-section"):
                yield Button("Resolve", id="resolve-btn", variant="primary")
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
        if event.button.id == "resolve-btn":
            self.resolve_hostname()
        elif event.button.id == "clear-btn":
            self.clear_results()
    
    def resolve_hostname(self) -> None:
        """Resolve the hostname using Phase 3 DNS utilities."""
        try:
            # Get hostname from input
            hostname_input = self.query_one("#hostname-input", Input)
            hostname = hostname_input.value.strip()
            
            # Validate input
            if not hostname:
                self.display_error("Please enter a hostname")
                self.set_status("Error: No hostname entered")
                return
            
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
            result = resolve_dns_hostname(
                hostname,
                timeout=5,
                include_reverse_dns=True
            )
            
            # Check if resolution was successful
            if result.status == DNSStatus.NOT_FOUND:
                self.display_error(f"Could not resolve {hostname}")
                self.set_status(f"Failed to resolve {hostname}")
                return
            
            if result.status == DNSStatus.TIMEOUT:
                self.display_error(f"DNS resolution timeout")
                self.set_status("Timeout - no response from DNS server")
                return
            
            if result.status == DNSStatus.ERROR:
                self.display_error(f"Error: {result.error_message}")
                self.set_status(f"Error: {result.error_message}")
                return
            
            # Display results based on query type
            record_count = 0
            
            # Add A records (IPv4)
            if query_type in ["A", "BOTH", "ALL"]:
                if result.ipv4_addresses:
                    for ip in result.ipv4_addresses:
                        # Find the record with this IP to get timing
                        record = next(
                            (r for r in result.records if r.value == ip and r.record_type == "A"),
                            None
                        )
                        self.results_widget.add_row(
                            type="A",
                            value=ip,
                            time=f"{record.query_time_ms:.2f}" if record else "N/A"
                        )
                        record_count += 1
            
            # Add AAAA records (IPv6)
            if query_type in ["AAAA", "BOTH", "ALL"]:
                if result.ipv6_addresses:
                    for ip in result.ipv6_addresses:
                        # Find the record with this IP to get timing
                        record = next(
                            (r for r in result.records if r.value == ip and r.record_type == "AAAA"),
                            None
                        )
                        self.results_widget.add_row(
                            type="AAAA",
                            value=ip,
                            time=f"{record.query_time_ms:.2f}" if record else "N/A"
                        )
                        record_count += 1
            
            # Add PTR record (Reverse DNS)
            if query_type in ["PTR", "ALL"]:
                if result.reverse_dns:
                    record = next(
                        (r for r in result.records if r.record_type == "PTR"),
                        None
                    )
                    self.results_widget.add_row(
                        type="PTR",
                        value=result.reverse_dns,
                        time=f"{record.query_time_ms:.2f}" if record else "N/A"
                    )
                    record_count += 1
            
            # Show success message
            if record_count > 0:
                self.display_success(
                    f"Resolved {hostname} - Found {record_count} record(s) "
                    f"in {result.lookup_time_ms:.2f}ms"
                )
                self.set_status(
                    f"✓ Resolved {hostname} - {record_count} records found"
                )
            else:
                self.display_error(f"No records found for {hostname}")
                self.set_status(f"No records found for {hostname}")
        
        except Exception as e:
            self.display_error(f"Error: {str(e)}")
            self.set_status(f"Error: {str(e)}")
    
    def clear_results(self) -> None:
        """Clear all results and inputs."""
        try:
            # Clear inputs
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
            self.display_error(f"Error clearing: {str(e)}")
