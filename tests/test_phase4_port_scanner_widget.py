"""Phase 4.3 Port Scanner Widget Tests.

Uses modern pytest patterns and parametrization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from tui.widgets.port_scanner_widget import PortScannerWidget

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture
def widget() -> PortScannerWidget:
    """PortScannerWidget instance for testing."""
    return PortScannerWidget()


class TestPortScannerWidgetInitialization:
    """Tests for PortScannerWidget initialization."""

    def test_widget_initialization(self, widget: PortScannerWidget) -> None:
        """Test widget initializes correctly."""
        assert widget.widget_name == "PortScannerWidget"
        assert widget.scan_in_progress is False

    def test_widget_initialization_with_id(self) -> None:
        """Test widget initializes correctly with an id."""
        widget_with_id = PortScannerWidget(id="test_port")
        assert widget_with_id.id == "test_port"

    def test_inherits_from_base_widget(self, widget: PortScannerWidget) -> None:
        """Test widget inherits from BaseWidget."""
        from tui.widgets.base import BaseWidget

        assert isinstance(widget, BaseWidget)


class TestPortParsingLogic:
    """Tests for port input parsing logic using parametrization."""

    @pytest.mark.parametrize(
        ("port_str", "expected"),
        [
            ("80", [80]),
            ("1", [1]),
            ("65535", [65535]),
            ("  443  ", [443]),
        ],
    )
    def test_parse_single_port_valid(self, widget: PortScannerWidget, port_str: str, expected: list[int]) -> None:
        """Test parsing valid single port strings."""
        assert widget.parse_ports_input(port_str, "single") == expected

    @pytest.mark.parametrize(
        "port_str",
        [
            "abc",
            "0",
            "65536",
            "-1",
            "",
            "   ",
        ],
    )
    def test_parse_single_port_invalid(self, widget: PortScannerWidget, port_str: str) -> None:
        """Test parsing invalid single port strings."""
        assert widget.parse_ports_input(port_str, "single") is None

    @pytest.mark.parametrize(
        ("port_str", "expected"),
        [
            ("80,443,22", [22, 80, 443]),
            ("80, 443, 22", [22, 80, 443]),
            ("80,443,80,22", [22, 80, 443]),  # Deduplication
            ("  22, 80  ", [22, 80]),
            ("80,,443", [80, 443]),  # Robustness to empty segments
        ],
    )
    def test_parse_multiple_ports_valid(self, widget: PortScannerWidget, port_str: str, expected: list[int]) -> None:
        """Test parsing valid multiple port strings."""
        assert widget.parse_ports_input(port_str, "multiple") == expected

    @pytest.mark.parametrize(
        "port_str",
        [
            "80,abc,443",
            "80,0,443",
            "80,70000",
            "",
            "   ",
        ],
    )
    def test_parse_multiple_ports_invalid(self, widget: PortScannerWidget, port_str: str) -> None:
        """Test parsing invalid multiple port strings."""
        assert widget.parse_ports_input(port_str, "multiple") is None

    @pytest.mark.parametrize(
        ("port_str", "expected_len"),
        [
            ("80-85", 6),
            ("80 - 85", 6),
            ("443-80", 364),  # Auto-swap
            ("80-80", 1),
            ("1-5000", 5000),
        ],
    )
    def test_parse_range_valid(self, widget: PortScannerWidget, port_str: str, expected_len: int) -> None:
        """Test parsing valid port range strings."""
        result = widget.parse_ports_input(port_str, "range")
        assert result is not None
        assert len(result) == expected_len
        assert sorted(result) == result

    @pytest.mark.parametrize(
        "port_str",
        [
            "80:443",
            "1-10000",  # Too large (> 5000)
            "0-80",
            "80-70000",
            "abc-def",
            "",
        ],
    )
    def test_parse_range_invalid(self, widget: PortScannerWidget, port_str: str) -> None:
        """Test parsing invalid range strings."""
        assert widget.parse_ports_input(port_str, "range") is None


class TestPortScannerBehavior:
    """Tests for widget behavior and state management."""

    def test_concurrency_guard(self, widget: PortScannerWidget, mocker: MockerFixture) -> None:
        """Test that scan_in_progress flag prevents concurrent scans."""
        widget.scan_in_progress = True
        mock_error = mocker.patch.object(widget, "display_error")

        widget.scan_ports()

        mock_error.assert_called_with("Scan already in progress")

    def test_clear_results(self, widget: PortScannerWidget, mocker: MockerFixture) -> None:
        """Test clearing inputs and results."""
        # Mock UI components
        mock_host = MagicMock()
        mock_port = MagicMock()
        mock_summary = MagicMock()
        mock_status = MagicMock()
        mock_error_display = MagicMock()

        # Flexible mock for query_one that handles expect_type keyword
        def mock_query(query: str, *args: Any, **kwargs: Any) -> Any:
            return {
                "#host-input": mock_host,
                "#port-input": mock_port,
                "#summary-label": mock_summary,
                "#status-label": mock_status,
                "#error-display": mock_error_display,
            }.get(query)

        mocker.patch.object(widget, "query_one", side_effect=mock_query)
        widget.results_widget = MagicMock()

        widget.clear_results()

        assert mock_host.value == ""
        assert mock_port.value == ""
        widget.results_widget.clear_results.assert_called_once()
        mock_summary.update.assert_called_with("")
        mock_status.update.assert_called_with("")
