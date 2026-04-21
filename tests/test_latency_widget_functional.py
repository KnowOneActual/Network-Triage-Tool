"""Functional tests for LatencyAnalyzerWidget using Textual's test framework."""

from unittest.mock import patch

import pytest
from textual.app import App, ComposeResult
from textual.widgets import DataTable

from src.shared.latency_utils import LatencyStatus, PingStatistics, TracerouteHop
from src.tui.widgets.latency_analyzer_widget import LatencyAnalyzerWidget


class LatencyMockApp(App):
    """Mock app for testing LatencyAnalyzerWidget."""

    def compose(self) -> ComposeResult:
        yield LatencyAnalyzerWidget()


@pytest.mark.asyncio
async def test_latency_analysis_success():
    """Test successful latency analysis in the UI."""
    app = LatencyMockApp()

    mock_hops = [
        TracerouteHop(
            hop_number=1,
            ip_address="192.168.1.1",
            hostname="router",
            rtt1_ms=1.0,
            rtt2_ms=1.1,
            rtt3_ms=1.2,
            status="responsive",
        ),
        TracerouteHop(
            hop_number=2,
            ip_address="8.8.8.8",
            hostname="google",
            rtt1_ms=15.0,
            rtt2_ms=15.1,
            rtt3_ms=15.2,
            status="responsive",
        ),
    ]
    mock_ping = PingStatistics(
        host="8.8.8.8",
        packets_sent=5,
        packets_received=5,
        min_ms=10.0,
        max_ms=20.0,
        avg_ms=15.0,
        stddev_ms=2.0,
        packet_loss_percent=0.0,
        status=LatencyStatus.SUCCESS,
        rtt_values=[10.0, 12.0, 15.0, 18.0, 20.0],
    )

    with (
        patch("src.tui.widgets.latency_analyzer_widget.mtr_style_trace", return_value=(mock_hops, "success")),
        patch("src.tui.widgets.latency_analyzer_widget.ping_statistics", return_value=mock_ping),
    ):
        async with app.run_test() as pilot:
            widget = app.query_one(LatencyAnalyzerWidget)

            # Set host
            widget.query_one("#host-input").value = "8.8.8.8"

            # Call display directly to simulate background thread completion in a sync way for test
            widget._display_results(mock_hops, mock_ping)

            table = widget.query_one("#hops-table", DataTable)
            assert table.row_count == 2

            # Check summary label exists
            summary = widget.query_one("#ping-summary-label")
            assert summary is not None


@pytest.mark.asyncio
async def test_latency_clear():
    """Test clearing latency results."""
    app = LatencyMockApp()

    async with app.run_test() as pilot:
        widget = app.query_one(LatencyAnalyzerWidget)

        # Set some values
        widget.query_one("#host-input").value = "8.8.8.8"
        table = widget.query_one("#hops-table", DataTable)
        table.add_row("1", "1.1.1.1", "host", "10ms", "0%")

        assert table.row_count == 1

        # Click Clear
        await pilot.click("#clear-btn")

        # Verify cleared
        assert widget.query_one("#host-input").value == ""
        assert table.row_count == 0


@pytest.mark.asyncio
async def test_validate_host_logic():
    """Test host validation helper."""
    assert LatencyAnalyzerWidget.validate_host("google.com")[0] is True
    assert LatencyAnalyzerWidget.validate_host("")[0] is False
    assert LatencyAnalyzerWidget.validate_host("a" * 300)[0] is False
    assert LatencyAnalyzerWidget.validate_host("host name")[0] is False
