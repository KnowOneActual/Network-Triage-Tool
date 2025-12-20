"""DNS Resolver Widget for Phase 4.2."""

from .base import BaseWidget
from .components import ResultsWidget, ResultColumn
from textual.app import ComposeResult
from textual.widgets import Input, Button, Label, Select
from textual.containers import Container, Horizontal, Vertical


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
                    ("CNAME", "CNAME"),
                    ("MX", "MX"),
                    ("NS", "NS"),
                    ("TXT", "TXT"),
                    ("SOA", "SOA"),
                    ("PTR", "PTR"),
                ],
                id="query-type-select",
                value="A"
            )
            
            # DNS server input (optional)
            yield Label("DNS Server (optional):")
            yield Input(
                id="dns-server-input",
                placeholder="8.8.8.8 or leave blank for system DNS",
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
            ResultColumn("TTL", "ttl", width=10),
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
        """Resolve the hostname."""
        try:
            hostname_input = self.query_one("#hostname-input", Input)
            hostname = hostname_input.value.strip()
            
            if not hostname:
                self.display_error("Please enter a hostname")
                self.set_status("Error: No hostname entered")
                return
            
            # Get query type
            query_type_select = self.query_one("#query-type-select", Select)
            query_type = query_type_select.value or "A"
            
            # Get optional DNS server
            dns_server_input = self.query_one("#dns-server-input", Input)
            dns_server = dns_server_input.value.strip() or None
            
            # Show loading state
            self.show_loading(f"Resolving {hostname} ({query_type})...")
            self.set_status(f"Resolving {hostname}...")
            
from src.shared.dns_utils import resolve_hostname as dns_resolve

result = await self.run_in_thread(
    dns_resolve,
    hostname,
    query_type=query_type
)

if result.success:
    self.results_widget.clear_results()
    for record in result.records:
        self.results_widget.add_row(
            type=record.type,
            value=record.value,
            ttl=record.ttl
        )
    self.display_success(f"Resolved {hostname}")
else:
    self.display_error(f"Failed: {result.error}")

            
            # Update status
            self.display_success(f"Ready to resolve {hostname}")
            self.set_status(f"Ready to resolve {hostname}")
        
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
