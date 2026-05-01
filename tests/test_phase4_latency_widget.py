"""Phase 4.4 Latency Analyzer Widget Tests."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tui.widgets.latency_analyzer_widget import LatencyAnalyzerWidget

# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestLatencyAnalyzerWidgetInitialization:
    """Tests for LatencyAnalyzerWidget initialization."""

    def test_widget_initialization(self):
        """Test widget initializes correctly."""
        widget = LatencyAnalyzerWidget()
        assert widget.widget_name == "LatencyAnalyzerWidget"

    def test_widget_initialization_with_id(self):
        """Test widget initializes correctly with an id."""
        widget = LatencyAnalyzerWidget(id="test_latency")
        assert widget.id == "test_latency"
        assert widget.widget_name == "LatencyAnalyzerWidget"

    def test_trace_in_progress_flag_initialized(self):
        """Test trace_in_progress flag is initialized to False."""
        widget = LatencyAnalyzerWidget()
        assert widget.trace_in_progress is False

    def test_inherits_from_base_widget(self):
        """Test widget inherits from BaseWidget."""
        from tui.widgets.base import BaseWidget

        widget = LatencyAnalyzerWidget()
        assert isinstance(widget, BaseWidget)

    def test_has_required_base_methods(self):
        """Test widget has required methods from BaseWidget."""
        widget = LatencyAnalyzerWidget()
        for method in ("display_error", "display_success", "show_loading", "set_status"):
            assert hasattr(widget, method)
            assert callable(getattr(widget, method))


# ---------------------------------------------------------------------------
# UI / Method presence
# ---------------------------------------------------------------------------


class TestLatencyAnalyzerUIMethods:
    """Tests for LatencyAnalyzerWidget method presence."""

    def test_has_compose_method(self):
        """Test widget has compose() method."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "compose") and callable(widget.compose)

    def test_has_button_handler(self):
        """Test widget has on_button_pressed handler."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "on_button_pressed") and callable(widget.on_button_pressed)

    def test_has_input_submitted_handler(self):
        """Test widget has on_input_submitted handler."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "on_input_submitted") and callable(widget.on_input_submitted)

    def test_has_run_analysis_method(self):
        """Test widget has run_analysis method."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "run_analysis") and callable(widget.run_analysis)

    def test_has_clear_results_method(self):
        """Test widget has clear_results method."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "clear_results") and callable(widget.clear_results)

    def test_has_validate_host_method(self):
        """Test widget has validate_host static method."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "validate_host") and callable(widget.validate_host)

    def test_has_format_rtt_method(self):
        """Test widget has format_rtt static method."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "format_rtt") and callable(widget.format_rtt)

    def test_has_color_rtt_method(self):
        """Test widget has color_rtt static method."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "color_rtt") and callable(widget.color_rtt)


# ---------------------------------------------------------------------------
# Host validation
# ---------------------------------------------------------------------------


class TestHostValidation:
    """Tests for LatencyAnalyzerWidget.validate_host()."""

    def test_empty_host_invalid(self):
        """Test that an empty string is invalid."""
        valid, msg = LatencyAnalyzerWidget.validate_host("")
        assert valid is False
        assert "enter" in msg.lower()

    def test_whitespace_only_invalid(self):
        """Test that whitespace-only input is invalid."""
        valid, msg = LatencyAnalyzerWidget.validate_host("   ")
        assert valid is False

    def test_valid_ip_address(self):
        """Test that a valid IPv4 address is accepted."""
        valid, msg = LatencyAnalyzerWidget.validate_host("8.8.8.8")
        assert valid is True
        assert msg == ""

    def test_valid_hostname(self):
        """Test that a valid hostname is accepted."""
        valid, msg = LatencyAnalyzerWidget.validate_host("google.com")
        assert valid is True
        assert msg == ""

    def test_host_with_spaces_invalid(self):
        """Test that a host containing spaces is invalid."""
        valid, msg = LatencyAnalyzerWidget.validate_host("google .com")
        assert valid is False
        assert "space" in msg.lower()

    def test_host_too_long_invalid(self):
        """Test that a host longer than 253 chars is invalid."""
        long_host = "a" * 254
        valid, msg = LatencyAnalyzerWidget.validate_host(long_host)
        assert valid is False
        assert "long" in msg.lower()

    def test_host_exactly_253_chars_valid(self):
        """Test that a host of exactly 253 chars passes length check."""
        host = "a" * 253
        valid, _ = LatencyAnalyzerWidget.validate_host(host)
        assert valid is True

    def test_localhost_valid(self):
        """Test that 'localhost' is accepted."""
        valid, msg = LatencyAnalyzerWidget.validate_host("localhost")
        assert valid is True
        assert msg == ""


# ---------------------------------------------------------------------------
# RTT formatting
# ---------------------------------------------------------------------------


class TestRTTFormatting:
    """Tests for LatencyAnalyzerWidget.format_rtt()."""

    def test_none_returns_timeout_marker(self):
        """Test that None RTT returns '***'."""
        assert LatencyAnalyzerWidget.format_rtt(None) == "***"

    def test_float_formatted_correctly(self):
        """Test that a float RTT is formatted with 1 decimal place."""
        result = LatencyAnalyzerWidget.format_rtt(12.3456)
        assert result == "12.3 ms"

    def test_zero_formatted_correctly(self):
        """Test that zero RTT formats correctly."""
        result = LatencyAnalyzerWidget.format_rtt(0.0)
        assert result == "0.0 ms"

    def test_large_rtt_formatted(self):
        """Test that a large RTT value is formatted."""
        result = LatencyAnalyzerWidget.format_rtt(1234.567)
        assert result == "1234.6 ms"

    def test_integer_value_formatted(self):
        """Test that an integer-like float formats as X.0 ms."""
        result = LatencyAnalyzerWidget.format_rtt(50.0)
        assert result == "50.0 ms"


# ---------------------------------------------------------------------------
# RTT colour markup
# ---------------------------------------------------------------------------


class TestRTTColoring:
    """Tests for LatencyAnalyzerWidget.color_rtt()."""

    def test_none_returns_dim(self):
        """Test that None RTT returns dim-markup timeout marker."""
        result = LatencyAnalyzerWidget.color_rtt(None)
        assert "[dim]" in result
        assert "***" in result

    def test_fast_rtt_green(self):
        """Test that RTT < 50 ms is coloured green."""
        result = LatencyAnalyzerWidget.color_rtt(10.0)
        assert "[green]" in result

    def test_boundary_just_below_50_green(self):
        """Test RTT of 49.9 ms is green."""
        result = LatencyAnalyzerWidget.color_rtt(49.9)
        assert "[green]" in result

    def test_medium_rtt_yellow(self):
        """Test that 50 ms ≤ RTT < 150 ms is yellow."""
        result = LatencyAnalyzerWidget.color_rtt(50.0)
        assert "[yellow]" in result

    def test_boundary_just_below_150_yellow(self):
        """Test RTT of 149.9 ms is yellow."""
        result = LatencyAnalyzerWidget.color_rtt(149.9)
        assert "[yellow]" in result

    def test_slow_rtt_red(self):
        """Test that RTT ≥ 150 ms is red."""
        result = LatencyAnalyzerWidget.color_rtt(150.0)
        assert "[red]" in result

    def test_very_slow_rtt_red(self):
        """Test that a very high RTT (500 ms) is red."""
        result = LatencyAnalyzerWidget.color_rtt(500.0)
        assert "[red]" in result

    def test_result_contains_ms(self):
        """Test that the coloured string contains the formatted value."""
        result = LatencyAnalyzerWidget.color_rtt(20.0)
        assert "20.0 ms" in result


# ---------------------------------------------------------------------------
# Phase 3 integration
# ---------------------------------------------------------------------------


class TestPhase3Integration:
    """Tests for integration with Phase 3 latency utilities."""

    def test_mtr_style_trace_importable(self):
        """Test that mtr_style_trace is importable from Phase 3."""
        from shared.latency_utils import mtr_style_trace

        assert callable(mtr_style_trace)

    def test_ping_statistics_importable(self):
        """Test that ping_statistics is importable from Phase 3."""
        from shared.latency_utils import ping_statistics

        assert callable(ping_statistics)

    def test_traceroute_hop_dataclass_structure(self):
        """Test TracerouteHop dataclass has expected fields."""
        from shared.latency_utils import TracerouteHop

        hop = TracerouteHop(
            hop_number=1,
            hostname="router.local",
            ip_address="192.168.1.1",
            rtt1_ms=5.0,
            rtt2_ms=6.0,
            rtt3_ms=5.5,
            status="responsive",
        )
        assert hop.hop_number == 1
        assert hop.ip_address == "192.168.1.1"
        assert hop.hostname == "router.local"
        assert hop.status == "responsive"

    def test_traceroute_hop_avg_rtt_with_values(self):
        """Test TracerouteHop.avg_rtt_ms() returns avg when values present."""
        from shared.latency_utils import TracerouteHop

        hop = TracerouteHop(1, None, "1.1.1.1", 10.0, 20.0, 30.0, "responsive")
        avg = hop.avg_rtt_ms()
        assert avg == pytest.approx(20.0)

    def test_traceroute_hop_avg_rtt_all_none(self):
        """Test TracerouteHop.avg_rtt_ms() returns None when all RTTs are None."""
        from shared.latency_utils import TracerouteHop

        hop = TracerouteHop(2, None, None, None, None, None, "timeout")
        assert hop.avg_rtt_ms() is None

    def test_ping_statistics_dataclass_fields(self):
        """Test PingStatistics dataclass has expected fields."""
        from shared.latency_utils import LatencyStatus, PingStatistics

        stats = PingStatistics(
            host="8.8.8.8",
            packets_sent=5,
            packets_received=5,
            packet_loss_percent=0.0,
            min_ms=10.0,
            avg_ms=12.0,
            max_ms=15.0,
            stddev_ms=1.5,
            status=LatencyStatus.SUCCESS,
            rtt_values=[10.0, 11.0, 12.0, 13.0, 14.0],
        )
        assert stats.host == "8.8.8.8"
        assert stats.packet_loss_percent == 0.0
        assert stats.avg_ms == 12.0

    def test_widget_imports_latency_utilities(self):
        """Test that the widget module exposes the latency utility imports."""
        import tui.widgets.latency_analyzer_widget as mod

        assert hasattr(mod, "mtr_style_trace_stream")
        assert hasattr(mod, "ping_statistics")
        assert hasattr(mod, "TracerouteHop")
        assert hasattr(mod, "PingStatistics")


# ---------------------------------------------------------------------------
# Foundation features
# ---------------------------------------------------------------------------


class TestLatencyAnalyzerFoundationFeatures:
    """Tests confirming Phase 4 foundation features are present."""

    def test_uses_base_widget_and_async_mixin(self):
        """Test widget uses BaseWidget and AsyncOperationMixin."""
        from tui.widgets.base import AsyncOperationMixin, BaseWidget

        widget = LatencyAnalyzerWidget()
        assert isinstance(widget, BaseWidget)
        assert isinstance(widget, AsyncOperationMixin)

    def test_has_caching_from_mixin(self):
        """Test widget has caching support from AsyncOperationMixin."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "cache_result") and callable(widget.cache_result)
        assert hasattr(widget, "get_cached") and callable(widget.get_cached)

    def test_has_progress_tracking(self):
        """Test widget has progress tracking from BaseWidget."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "is_loading")
        assert hasattr(widget, "show_loading") and callable(widget.show_loading)

    def test_has_status_management(self):
        """Test widget has status management from BaseWidget."""
        widget = LatencyAnalyzerWidget()
        assert hasattr(widget, "current_status")
        assert hasattr(widget, "set_status") and callable(widget.set_status)


# ---------------------------------------------------------------------------
# Concurrency guard
# ---------------------------------------------------------------------------


class TestConcurrencyGuard:
    """Test that trace_in_progress prevents duplicate runs."""

    def test_concurrent_run_blocked(self):
        """Test that running analysis while one is in progress shows an error."""
        widget = LatencyAnalyzerWidget()
        widget.trace_in_progress = True

        with patch.object(widget, "display_error") as mock_error:
            widget.run_analysis()
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "progress" in call_args.lower()

    def test_trace_in_progress_false_by_default(self):
        """Test that the flag starts False and allows analysis to proceed."""
        widget = LatencyAnalyzerWidget()
        assert widget.trace_in_progress is False


# ---------------------------------------------------------------------------
# Docstrings
# ---------------------------------------------------------------------------


class TestDocstrings:
    """Test that public methods have docstrings."""

    def test_class_has_docstring(self):
        """Test the widget class has a docstring."""
        assert LatencyAnalyzerWidget.__doc__ is not None
        assert len(LatencyAnalyzerWidget.__doc__) > 0

    def test_run_analysis_has_docstring(self):
        """Test run_analysis method has a docstring."""
        assert LatencyAnalyzerWidget.run_analysis.__doc__ is not None

    def test_clear_results_has_docstring(self):
        """Test clear_results method has a docstring."""
        assert LatencyAnalyzerWidget.clear_results.__doc__ is not None

    def test_validate_host_has_docstring(self):
        """Test validate_host method has a docstring."""
        assert LatencyAnalyzerWidget.validate_host.__doc__ is not None

    def test_format_rtt_has_docstring(self):
        """Test format_rtt method has a docstring."""
        assert LatencyAnalyzerWidget.format_rtt.__doc__ is not None

    def test_color_rtt_has_docstring(self):
        """Test color_rtt method has a docstring."""
        assert LatencyAnalyzerWidget.color_rtt.__doc__ is not None
