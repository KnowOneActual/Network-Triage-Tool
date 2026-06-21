"""Tests for Phase 5 Traffic Health monitor and widget."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from network_triage.shared.traffic_health import (
    HISTORY_FILE,
    TrafficHealthMonitor,
)
from tui.widgets.traffic_health_widget import TrafficHealthWidget


class TrafficHealthApp(App):
    """Test app wrapper for TrafficHealthWidget."""

    def compose(self) -> ComposeResult:
        yield TrafficHealthWidget(id="tool_traffic")


@pytest.fixture
def clean_history(tmp_path, monkeypatch):
    """Fixture to mock the history file path to a temp dir."""
    mock_history_dir = tmp_path / "config"
    mock_history_file = mock_history_dir / "traffic_history.json"

    # Patch the global history path constants in the traffic_health module
    monkeypatch.setattr(
        "network_triage.shared.traffic_health.HISTORY_DIR", mock_history_dir
    )
    monkeypatch.setattr(
        "network_triage.shared.traffic_health.HISTORY_FILE", mock_history_file
    )

    return mock_history_file


def test_monitor_initial_state():
    """Test initial state of TrafficHealthMonitor."""
    monitor = TrafficHealthMonitor()
    assert monitor.total_packets == 0
    assert monitor.unicast_packets == 0
    assert monitor.broadcast_packets == 0
    assert monitor.multicast_packets == 0
    assert monitor.arp_packets == 0
    assert monitor.dhcp_packets == 0
    assert monitor.is_running is False
    assert monitor.is_simulated is False


def test_monitor_reset():
    """Test reset method resets all counters."""
    monitor = TrafficHealthMonitor()
    monitor.total_packets = 10
    monitor.unicast_packets = 5
    monitor.broadcast_packets = 5
    monitor.arp_packets = 2

    monitor.reset()
    assert monitor.total_packets == 0
    assert monitor.unicast_packets == 0
    assert monitor.broadcast_packets == 0
    assert monitor.arp_packets == 0


def test_monitor_simulation_fallback():
    """Test that TrafficHealthMonitor falls back to simulation when raw socket fails."""
    monitor = TrafficHealthMonitor()

    # Mock scapy sniff to raise PermissionError, causing simulation mode to kick in
    with patch(
        "network_triage.shared.traffic_health.sniff",
        side_effect=PermissionError("Operation not permitted"),
    ):
        packet_updates = []

        def callback(m):
            packet_updates.append(m.get_stats())
            if m.total_packets >= 5:
                m.stop()

        monitor.start(callback=callback)

        # Wait briefly for simulation thread to run and update packets
        import time

        start_wait = time.time()
        while monitor.is_running and time.time() - start_wait < 5.0:
            time.sleep(0.1)

        monitor.stop()

        assert monitor.is_simulated is True
        assert len(packet_updates) > 0
        final_stats = monitor.get_stats()
        assert final_stats["total_packets"] > 0
        assert final_stats["is_simulated"] is True


def test_monitor_history_saving_and_loading(clean_history):
    """Test saving stats to history and loading it back."""
    monitor = TrafficHealthMonitor()
    monitor.total_packets = 100
    monitor.unicast_packets = 80
    monitor.broadcast_packets = 20
    monitor.is_simulated = True

    # Save to history
    monitor.save_to_history()

    # Load and verify
    history = monitor.load_history()
    assert len(history) == 1
    assert history[0]["total_packets"] == 100
    assert history[0]["unicast_packets"] == 80
    assert history[0]["is_simulated"] is True
    assert "timestamp" in history[0]


def test_monitor_comparison(clean_history):
    """Test baseline historical comparison."""
    monitor = TrafficHealthMonitor()
    from datetime import datetime, timedelta

    # Write a simulated history record from "yesterday" (e.g. 24 hours ago)
    yesterday_time = (datetime.now() - timedelta(hours=24)).isoformat()
    yesterday_record = {
        "total_packets": 200,
        "unicast_packets": 150,
        "broadcast_packets": 40,
        "multicast_packets": 10,
        "packets_per_second": 5.0,
        "timestamp": yesterday_time,
        "is_simulated": True,
    }

    clean_history.parent.mkdir(parents=True, exist_ok=True)
    with open(clean_history, "w", encoding="utf-8") as f:
        json.dump([yesterday_record], f)

    comparison = monitor.get_yesterday_comparison()
    assert comparison is not None
    assert comparison["total_packets"] == 200
    assert comparison["packets_per_second"] == 5.0


@pytest.mark.asyncio
async def test_widget_mount(clean_history):
    """Test mounting TrafficHealthWidget."""
    app = TrafficHealthApp()
    async with app.run_test() as pilot:
        widget = app.query_one(TrafficHealthWidget)
        assert widget is not None
        assert widget.current_status == "Ready"

        # Check UI components
        assert widget.query_one("#traffic-start-btn") is not None
        assert widget.query_one("#traffic-stop-btn").disabled is True
        assert widget.query_one("#traffic-save-btn").disabled is True


@pytest.mark.asyncio
async def test_widget_sniff_cycle(clean_history):
    """Test start and stop cycle of the TrafficHealthWidget."""
    app = TrafficHealthApp()
    async with app.run_test() as pilot:
        widget = app.query_one(TrafficHealthWidget)

        # Mock start/stop sniffing to run instantly
        with patch.object(
            widget.monitor, "start"
        ) as mock_start, patch.object(widget.monitor, "stop") as mock_stop:
            await pilot.click("#traffic-start-btn")
            assert mock_start.called

            # Widget state should update
            assert widget.query_one("#traffic-start-btn").disabled is True
            assert widget.query_one("#traffic-stop-btn").disabled is False

            # Simulate stopping
            await pilot.click("#traffic-stop-btn")
            # Wait for thread tasks
            await pilot.pause()

            assert mock_stop.called


@pytest.mark.asyncio
async def test_widget_ui_updates(clean_history):
    """Test that widget updates display texts on receiving packet updates."""
    app = TrafficHealthApp()
    async with app.run_test() as pilot:
        widget = app.query_one(TrafficHealthWidget)

        # Mock stats payload
        simulated_stats = {
            "total_packets": 10,
            "unicast_packets": 6,
            "multicast_packets": 2,
            "broadcast_packets": 2,
            "arp_packets": 1,
            "dhcp_packets": 1,
            "stp_packets": 0,
            "lldp_packets": 0,
            "cdp_packets": 0,
            "ipv4_packets": 8,
            "ipv6_packets": 2,
            "tcp_packets": 5,
            "udp_packets": 3,
            "icmp_packets": 2,
            "dns_packets": 1,
            "elapsed_seconds": 2.5,
            "packets_per_second": 4.0,
            "is_simulated": True,
        }

        # Directly call update UI handler to test formatting
        widget.update_ui_stats(simulated_stats)

        dist_details = widget.query_one("#dist-details", Static)
        proto_details = widget.query_one("#proto-details", Static)

        # Validate that texts contain the counts
        assert "Total Packets: 10" in str(dist_details.render())
        assert "Rate: 4.0 pps" in str(dist_details.render())
        assert "Unicast: 6 packets" in str(dist_details.render())
        assert "Broadcast: 2 packets" in str(dist_details.render())

        assert "ARP: 1" in str(proto_details.render())
        assert "DHCP/BOOTP: 1" in str(proto_details.render())
        assert "IPv4: 8" in str(proto_details.render())


@pytest.mark.asyncio
async def test_widget_clear(clean_history):
    """Test clearing statistics in the widget."""
    app = TrafficHealthApp()
    async with app.run_test() as pilot:
        widget = app.query_one(TrafficHealthWidget)

        # Mock last stats
        widget._last_stats = {"total_packets": 5}
        widget.query_one("#traffic-save-btn").disabled = False

        await pilot.click("#traffic-clear-btn")

        assert widget._last_stats == {}
        assert widget.query_one("#traffic-save-btn").disabled is True
        assert (
            "Start monitoring"
            in str(widget.query_one("#dist-details", Static).render())
        )
