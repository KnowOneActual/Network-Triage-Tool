"""Functional tests for DNSResolverWidget using Textual's test framework."""

import pytest
from textual.app import App, ComposeResult
from unittest.mock import MagicMock, patch
from src.tui.widgets.dns_resolver_widget import DNSResolverWidget
from src.shared.dns_utils import DNSStatus, DNSLookupResult, DNSRecord

class DNSMockApp(App):
    """Mock app for testing DNSResolverWidget."""
    def compose(self) -> ComposeResult:
        yield DNSResolverWidget()

@pytest.mark.asyncio
async def test_dns_resolution_success():
    """Test successful DNS resolution in the UI."""
    app = DNSMockApp()
    
    # Mock result
    mock_result = DNSLookupResult(
        hostname="example.com",
        ipv4_addresses=["93.184.216.34"],
        ipv6_addresses=[],
        reverse_dns=None,
        lookup_time_ms=10.5,
        status=DNSStatus.SUCCESS,
        records=[DNSRecord("A", "93.184.216.34", 10.5, DNSStatus.SUCCESS)]
    )

    with patch("src.tui.widgets.dns_resolver_widget.resolve_dns_hostname", return_value=mock_result):
        async with app.run_test() as pilot:
            widget = app.query_one(DNSResolverWidget)
            
            # Set hostname
            await pilot.click("#hostname-input")
            await pilot.press(*"example.com")
            
            # Click Resolve
            await pilot.click("#resolve-btn")
            
            # Verify results widget has rows
            assert widget.results_widget.row_count == 1
            
            # Check cell content
            assert widget.results_widget.get_cell(str(1), "value") == "93.184.216.34"

@pytest.mark.asyncio
async def test_dns_clear():
    """Test clearing DNS results."""
    app = DNSMockApp()
    
    async with app.run_test() as pilot:
        widget = app.query_one(DNSResolverWidget)
        
        # Set some values
        widget.query_one("#hostname-input").value = "test.com"
        widget.results_widget.add_row(type="A", value="1.1.1.1", time="1.0")
        
        assert widget.query_one("#hostname-input").value == "test.com"
        assert widget.results_widget.row_count == 1
        
        # Click Clear
        await pilot.click("#clear-btn")
        
        # Verify cleared
        assert widget.query_one("#hostname-input").value == ""
        assert widget.results_widget.row_count == 0

@pytest.mark.asyncio
async def test_dns_resolution_no_input():
    """Test DNS resolution with no input."""
    app = DNSMockApp()
    
    async with app.run_test() as pilot:
        widget = app.query_one(DNSResolverWidget)
        
        # Click Resolve with empty input
        await pilot.click("#resolve-btn")
        
        # Should stay at 0 rows
        assert widget.results_widget.row_count == 0

@pytest.mark.asyncio
async def test_dns_resolution_not_found():
    """Test DNS resolution when host not found."""
    app = DNSMockApp()
    
    mock_result = DNSLookupResult(
        hostname="nonexistent.local",
        ipv4_addresses=[],
        ipv6_addresses=[],
        reverse_dns=None,
        lookup_time_ms=5.0,
        status=DNSStatus.NOT_FOUND
    )

    with patch("src.tui.widgets.dns_resolver_widget.resolve_dns_hostname", return_value=mock_result):
        async with app.run_test() as pilot:
            widget = app.query_one(DNSResolverWidget)
            widget.query_one("#hostname-input").value = "nonexistent.local"
            
            await pilot.click("#resolve-btn")
            
            assert widget.results_widget.row_count == 0
