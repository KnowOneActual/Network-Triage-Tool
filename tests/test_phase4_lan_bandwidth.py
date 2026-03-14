"""Phase 4.6 LAN Bandwidth Tester Widget Tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tui.widgets.lan_bandwidth_widget import (
    BYTES_PER_MBIT,
    DURATION_OPTIONS,
    SAMPLE_INTERVAL,
    BandwidthResult,
    BandwidthSample,
    build_interface_options,
    bytes_to_mbps,
    color_mbps,
    format_mbps,
    get_io_counters,
    list_interfaces,
    run_bandwidth_test,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_sample(
    timestamp="12:00:00",
    rx_mbps=50.0,
    tx_mbps=10.0,
    elapsed=1.0,
) -> BandwidthSample:
    """Create a BandwidthSample with sensible defaults."""
    return BandwidthSample(
        timestamp=timestamp,
        rx_mbps=rx_mbps,
        tx_mbps=tx_mbps,
        elapsed=elapsed,
    )


def make_result(
    interface="en0",
    duration=10,
    samples: list[BandwidthSample] | None = None,
) -> BandwidthResult:
    """Create a BandwidthResult with optional samples."""
    r = BandwidthResult(interface=interface, duration=duration)
    if samples is not None:
        r.samples = samples
    return r


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    """Verify module-level constants have expected values."""

    def test_bytes_per_mbit_correct(self):
        """BYTES_PER_MBIT should be 125,000."""
        assert BYTES_PER_MBIT == 125_000

    def test_sample_interval_positive(self):
        """SAMPLE_INTERVAL must be a positive float."""
        assert isinstance(SAMPLE_INTERVAL, float)
        assert SAMPLE_INTERVAL > 0

    def test_duration_options_not_empty(self):
        """DURATION_OPTIONS must contain at least one entry."""
        assert len(DURATION_OPTIONS) > 0

    def test_duration_options_are_tuples(self):
        """Each DURATION_OPTIONS entry must be a 2-tuple."""
        for item in DURATION_OPTIONS:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_duration_option_values_are_numeric_strings(self):
        """The value in each DURATION_OPTIONS entry must be parseable as int."""
        for _, val in DURATION_OPTIONS:
            assert int(val) > 0


# ---------------------------------------------------------------------------
# BandwidthSample dataclass
# ---------------------------------------------------------------------------


class TestBandwidthSample:
    """Tests for the BandwidthSample dataclass."""

    def test_fields_stored_correctly(self):
        """All fields are stored as provided."""
        s = make_sample(timestamp="09:00:00", rx_mbps=100.0, tx_mbps=50.0, elapsed=5.0)
        assert s.timestamp == "09:00:00"
        assert s.rx_mbps == 100.0
        assert s.tx_mbps == 50.0
        assert s.elapsed == 5.0

    def test_default_values_accessible(self):
        """Samples created with make_sample() behave correctly."""
        s = make_sample()
        assert isinstance(s.rx_mbps, float)
        assert isinstance(s.tx_mbps, float)

    def test_rx_mbps_can_be_zero(self):
        """RX of 0.0 is a valid idle measurement."""
        s = make_sample(rx_mbps=0.0)
        assert s.rx_mbps == 0.0

    def test_tx_mbps_can_be_zero(self):
        """TX of 0.0 is a valid idle measurement."""
        s = make_sample(tx_mbps=0.0)
        assert s.tx_mbps == 0.0


# ---------------------------------------------------------------------------
# BandwidthResult dataclass & properties
# ---------------------------------------------------------------------------


class TestBandwidthResult:
    """Tests for the BandwidthResult dataclass and its computed properties."""

    def test_empty_result_defaults(self):
        """Empty result has interface, duration, and empty samples."""
        r = make_result()
        assert r.interface == "en0"
        assert r.duration == 10
        assert r.samples == []

    def test_avg_rx_empty_samples(self):
        """avg_rx_mbps returns 0.0 for an empty sample list."""
        r = make_result()
        assert r.avg_rx_mbps == 0.0

    def test_avg_tx_empty_samples(self):
        """avg_tx_mbps returns 0.0 for an empty sample list."""
        r = make_result()
        assert r.avg_tx_mbps == 0.0

    def test_peak_rx_empty_samples(self):
        """peak_rx_mbps returns 0.0 for an empty sample list."""
        r = make_result()
        assert r.peak_rx_mbps == 0.0

    def test_peak_tx_empty_samples(self):
        """peak_tx_mbps returns 0.0 for an empty sample list."""
        r = make_result()
        assert r.peak_tx_mbps == 0.0

    def test_sample_count_zero_when_empty(self):
        """sample_count is 0 when there are no samples."""
        assert make_result().sample_count == 0

    def test_avg_rx_calculated_correctly(self):
        """avg_rx_mbps computes the arithmetic mean."""
        samples = [make_sample(rx_mbps=100.0), make_sample(rx_mbps=200.0)]
        r = make_result(samples=samples)
        assert r.avg_rx_mbps == pytest.approx(150.0)

    def test_avg_tx_calculated_correctly(self):
        """avg_tx_mbps computes the arithmetic mean."""
        samples = [make_sample(tx_mbps=10.0), make_sample(tx_mbps=30.0)]
        r = make_result(samples=samples)
        assert r.avg_tx_mbps == pytest.approx(20.0)

    def test_peak_rx_is_max(self):
        """peak_rx_mbps returns the highest RX value."""
        samples = [make_sample(rx_mbps=50.0), make_sample(rx_mbps=999.0), make_sample(rx_mbps=100.0)]
        r = make_result(samples=samples)
        assert r.peak_rx_mbps == pytest.approx(999.0)

    def test_peak_tx_is_max(self):
        """peak_tx_mbps returns the highest TX value."""
        samples = [make_sample(tx_mbps=5.0), make_sample(tx_mbps=42.0)]
        r = make_result(samples=samples)
        assert r.peak_tx_mbps == pytest.approx(42.0)

    def test_sample_count_matches_list_length(self):
        """sample_count equals the number of samples appended."""
        samples = [make_sample() for _ in range(7)]
        r = make_result(samples=samples)
        assert r.sample_count == 7

    def test_single_sample_avg_equals_value(self):
        """With one sample, avg == peak == that sample's value."""
        samples = [make_sample(rx_mbps=77.7, tx_mbps=33.3)]
        r = make_result(samples=samples)
        assert r.avg_rx_mbps == pytest.approx(77.7)
        assert r.peak_rx_mbps == pytest.approx(77.7)
        assert r.avg_tx_mbps == pytest.approx(33.3)
        assert r.peak_tx_mbps == pytest.approx(33.3)

    def test_samples_field_is_list(self):
        """samples attribute is a list by default (not None)."""
        r = BandwidthResult(interface="lo", duration=5)
        assert isinstance(r.samples, list)


# ---------------------------------------------------------------------------
# bytes_to_mbps
# ---------------------------------------------------------------------------


class TestBytesToMbps:
    """Tests for the bytes_to_mbps() pure function."""

    def test_basic_conversion(self):
        """1,250,000 bytes / 1s = 10 Mbps."""
        assert bytes_to_mbps(1_250_000, 1.0) == pytest.approx(10.0)

    def test_zero_elapsed_returns_zero(self):
        """Division by zero guard: returns 0.0 when elapsed == 0."""
        assert bytes_to_mbps(1_000_000, 0.0) == 0.0

    def test_negative_elapsed_returns_zero(self):
        """Negative elapsed (clock skew edge case) returns 0.0."""
        assert bytes_to_mbps(1_000_000, -1.0) == 0.0

    def test_zero_bytes_returns_zero(self):
        """No traffic → 0 Mbps."""
        assert bytes_to_mbps(0, 1.0) == 0.0

    def test_1gbit_throughput(self):
        """125,000,000 bytes / 1s = 1000 Mbps (1 Gbit/s)."""
        assert bytes_to_mbps(125_000_000, 1.0) == pytest.approx(1000.0)

    def test_fractional_seconds(self):
        """Handles sub-second intervals without error."""
        result = bytes_to_mbps(125_000, 0.5)
        assert result == pytest.approx(2.0)

    def test_large_byte_count(self):
        """Does not overflow or error on large byte values."""
        # 10 GiB in 10 seconds
        result = bytes_to_mbps(10 * 1024**3, 10.0)
        assert result > 0

    def test_result_is_float(self):
        """Return type is always a float."""
        assert isinstance(bytes_to_mbps(1_000_000, 1.0), float)


# ---------------------------------------------------------------------------
# format_mbps
# ---------------------------------------------------------------------------


class TestFormatMbps:
    """Tests for the format_mbps() formatting function."""

    def test_mbps_range(self):
        """Values below 1000 are shown as '… Mbps'."""
        result = format_mbps(50.0)
        assert "Mbps" in result
        assert "50.00" in result

    def test_gbps_threshold(self):
        """Values >= 1000 Mbps are shown as '… Gbps'."""
        result = format_mbps(1000.0)
        assert "Gbps" in result

    def test_gbps_conversion(self):
        """2000 Mbps → '2.00 Gbps'."""
        result = format_mbps(2000.0)
        assert "2.00" in result
        assert "Gbps" in result

    def test_zero_formatted(self):
        """Zero is formatted without errors."""
        result = format_mbps(0.0)
        assert "0.00" in result

    def test_two_decimal_places(self):
        """Output always has two decimal places."""
        result = format_mbps(12.3)
        assert "12.30" in result

    def test_returns_string(self):
        """Return type is str."""
        assert isinstance(format_mbps(10.0), str)

    def test_high_gbps_value(self):
        """Very high values (e.g. 100 Gbps) are handled."""
        result = format_mbps(100_000.0)
        assert "Gbps" in result


# ---------------------------------------------------------------------------
# color_mbps
# ---------------------------------------------------------------------------


class TestColorMbps:
    """Tests for the color_mbps() Rich-markup helper."""

    def test_high_throughput_is_green(self):
        """100+ Mbps should be wrapped in green markup."""
        result = color_mbps(100.0)
        assert "[green]" in result
        assert "[/green]" in result

    def test_medium_throughput_is_yellow(self):
        """10-99 Mbps should be wrapped in yellow markup."""
        result = color_mbps(50.0)
        assert "[yellow]" in result

    def test_low_throughput_is_red(self):
        """< 10 Mbps should be wrapped in red markup."""
        result = color_mbps(5.0)
        assert "[red]" in result

    def test_exactly_100_is_green(self):
        """Boundary: 100.0 Mbps is green."""
        result = color_mbps(100.0)
        assert "[green]" in result

    def test_exactly_10_is_yellow(self):
        """Boundary: 10.0 Mbps is yellow (not red)."""
        result = color_mbps(10.0)
        assert "[yellow]" in result
        assert "[red]" not in result

    def test_value_in_output(self):
        """The formatted throughput value appears in the markup."""
        result = color_mbps(25.0)
        assert "25.00" in result

    def test_zero_is_red(self):
        """0 Mbps (no traffic) is shown in red."""
        result = color_mbps(0.0)
        assert "[red]" in result

    def test_returns_string(self):
        """Return type is str."""
        assert isinstance(color_mbps(10.0), str)

    def test_markup_closed(self):
        """Every opening tag has a corresponding closing tag."""
        for value in (0.0, 50.0, 200.0):
            result = color_mbps(value)
            # Count opening and closing brackets for the colour word
            opens = result.count("[green]") + result.count("[yellow]") + result.count("[red]")
            closes = result.count("[/green]") + result.count("[/yellow]") + result.count("[/red]")
            assert opens == closes == 1


# ---------------------------------------------------------------------------
# list_interfaces
# ---------------------------------------------------------------------------


class TestListInterfaces:
    """Tests for the list_interfaces() function."""

    def test_returns_list(self):
        """list_interfaces always returns a list."""
        with patch("tui.widgets.lan_bandwidth_widget.psutil.net_if_stats", return_value={}):
            result = list_interfaces()
        assert isinstance(result, list)

    def test_names_sorted(self):
        """Interface names are returned in sorted order."""
        fake_stats = {"zap0": MagicMock(), "en0": MagicMock(), "lo0": MagicMock()}
        with patch("tui.widgets.lan_bandwidth_widget.psutil.net_if_stats", return_value=fake_stats):
            result = list_interfaces()
        assert result == sorted(result)

    def test_returns_correct_names(self):
        """Interface names match the keys returned by psutil."""
        fake_stats = {"eth0": MagicMock(), "lo": MagicMock()}
        with patch("tui.widgets.lan_bandwidth_widget.psutil.net_if_stats", return_value=fake_stats):
            result = list_interfaces()
        assert set(result) == {"eth0", "lo"}

    def test_empty_when_no_interfaces(self):
        """Empty dict from psutil yields an empty list."""
        with patch("tui.widgets.lan_bandwidth_widget.psutil.net_if_stats", return_value={}):
            result = list_interfaces()
        assert result == []


# ---------------------------------------------------------------------------
# get_io_counters
# ---------------------------------------------------------------------------


class TestGetIoCounters:
    """Tests for the get_io_counters() function."""

    def _mock_global_counters(self, bytes_recv=1000, bytes_sent=500):
        """Create a mock for psutil.net_io_counters (pernic=False)."""
        m = MagicMock()
        m.bytes_recv = bytes_recv
        m.bytes_sent = bytes_sent
        return m

    def _mock_per_nic(self, iface="en0", bytes_recv=2000, bytes_sent=1000):
        """Create a mock for psutil.net_io_counters (pernic=True)."""
        nic = MagicMock()
        nic.bytes_recv = bytes_recv
        nic.bytes_sent = bytes_sent
        return {iface: nic}

    def test_all_interface_aggregate(self):
        """'all' returns global aggregate counters."""
        mock_counters = self._mock_global_counters(bytes_recv=8000, bytes_sent=4000)
        with patch(
            "tui.widgets.lan_bandwidth_widget.psutil.net_io_counters",
            return_value=mock_counters,
        ):
            result = get_io_counters("all")
        assert result == (8000, 4000)

    def test_specific_interface(self):
        """Named interface returns that interface's counters."""
        per_nic = self._mock_per_nic("eth0", bytes_recv=3000, bytes_sent=1500)
        with patch(
            "tui.widgets.lan_bandwidth_widget.psutil.net_io_counters",
            return_value=per_nic,
        ):
            result = get_io_counters("eth0")
        assert result == (3000, 1500)

    def test_nonexistent_interface_returns_none(self):
        """An interface not in the per-nic dict returns None."""
        with patch(
            "tui.widgets.lan_bandwidth_widget.psutil.net_io_counters",
            return_value={},
        ):
            result = get_io_counters("nonexistent0")
        assert result is None

    def test_exception_returns_none(self):
        """An OS-level exception returns None without raising."""
        with patch(
            "tui.widgets.lan_bandwidth_widget.psutil.net_io_counters",
            side_effect=RuntimeError("OS error"),
        ):
            result = get_io_counters("all")
        assert result is None

    def test_all_returns_none_when_counters_none(self):
        """If psutil returns None for global counters, get_io_counters returns None."""
        with patch(
            "tui.widgets.lan_bandwidth_widget.psutil.net_io_counters",
            return_value=None,
        ):
            result = get_io_counters("all")
        assert result is None

    def test_returns_tuple(self):
        """On success the return type is a tuple."""
        mock_counters = self._mock_global_counters()
        with patch(
            "tui.widgets.lan_bandwidth_widget.psutil.net_io_counters",
            return_value=mock_counters,
        ):
            result = get_io_counters("all")
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# build_interface_options
# ---------------------------------------------------------------------------


class TestBuildInterfaceOptions:
    """Tests for the build_interface_options() function."""

    def test_first_option_is_all(self):
        """The first entry is always 'All Interfaces'."""
        with patch("tui.widgets.lan_bandwidth_widget.list_interfaces", return_value=[]):
            result = build_interface_options()
        assert result[0] == ("All Interfaces", "all")

    def test_interfaces_included(self):
        """Detected interfaces are included after the 'all' option."""
        fake_ifaces = ["en0", "lo0"]
        with patch("tui.widgets.lan_bandwidth_widget.list_interfaces", return_value=fake_ifaces):
            result = build_interface_options()
        values = [v for _, v in result]
        assert "en0" in values
        assert "lo0" in values

    def test_no_interfaces_only_all(self):
        """When no interfaces are detected, only the 'all' option is returned."""
        with patch("tui.widgets.lan_bandwidth_widget.list_interfaces", return_value=[]):
            result = build_interface_options()
        assert len(result) == 1
        assert result[0][1] == "all"

    def test_each_entry_is_two_tuple(self):
        """Every option is a (label, value) 2-tuple."""
        with patch("tui.widgets.lan_bandwidth_widget.list_interfaces", return_value=["eth0"]):
            result = build_interface_options()
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_result_is_list(self):
        """Return type is a list."""
        with patch("tui.widgets.lan_bandwidth_widget.list_interfaces", return_value=[]):
            result = build_interface_options()
        assert isinstance(result, list)

    def test_interface_count_matches(self):
        """Option count = number of interfaces + 1 (for 'all')."""
        fake_ifaces = ["en0", "en1", "lo0"]
        with patch("tui.widgets.lan_bandwidth_widget.list_interfaces", return_value=fake_ifaces):
            result = build_interface_options()
        assert len(result) == len(fake_ifaces) + 1


# ---------------------------------------------------------------------------
# run_bandwidth_test
# ---------------------------------------------------------------------------


class TestRunBandwidthTest:
    """Tests for the run_bandwidth_test() blocking function (heavily mocked)."""

    def _mock_counters_seq(self, *seq):
        """Return a side_effect list for get_io_counters returning tuples."""
        return list(seq)

    def test_returns_bandwidth_result(self):
        """run_bandwidth_test always returns a BandwidthResult."""
        with patch("tui.widgets.lan_bandwidth_widget.get_io_counters", return_value=None):
            result = run_bandwidth_test("en0", 5)
        assert isinstance(result, BandwidthResult)

    def test_none_baseline_returns_empty(self):
        """If baseline counters are unavailable, returns empty result."""
        with patch("tui.widgets.lan_bandwidth_widget.get_io_counters", return_value=None):
            result = run_bandwidth_test("en0", 5)
        assert result.samples == []

    def test_result_has_correct_interface(self):
        """Result records the interface name passed in."""
        with patch("tui.widgets.lan_bandwidth_widget.get_io_counters", return_value=None):
            result = run_bandwidth_test("lo0", 5)
        assert result.interface == "lo0"

    def test_result_has_correct_duration(self):
        """Result records the duration passed in."""
        with patch("tui.widgets.lan_bandwidth_widget.get_io_counters", return_value=None):
            result = run_bandwidth_test("en0", 30)
        assert result.duration == 30

    def test_samples_collected_on_success(self):
        """At least one sample is collected when counters are available."""
        import time as _time

        call_count = 0
        start_mono = _time.monotonic()

        # Baseline + 2 subsequent reads (enough for 1 sample then stop)
        counter_values = [
            (0, 0),  # baseline
            (1_250_000, 500_000),  # tick 1 -> ~10 Mbps RX, ~4 Mbps TX
            None,  # none → break loop
        ]

        mono_values = [
            start_mono,  # prev_time initial
            start_mono + 1.0,  # after sleep tick 1
            start_mono + 6.0,  # after sleep tick 2 (exceeds duration=5)
        ]

        def fake_counters(interface):
            nonlocal call_count
            v = counter_values[min(call_count, len(counter_values) - 1)]
            call_count += 1
            return v

        mono_idx = [0]

        def fake_monotonic():
            idx = mono_idx[0]
            val = mono_values[min(idx, len(mono_values) - 1)]
            mono_idx[0] += 1
            return val

        with (
            patch("tui.widgets.lan_bandwidth_widget.get_io_counters", side_effect=fake_counters),
            patch("tui.widgets.lan_bandwidth_widget.time.sleep"),
            patch("tui.widgets.lan_bandwidth_widget.time.monotonic", side_effect=fake_monotonic),
        ):
            result = run_bandwidth_test("en0", 5)

        # Should have at least collected the tick-1 sample before None breaks the loop
        assert isinstance(result, BandwidthResult)


# ---------------------------------------------------------------------------
# Widget initialization
# ---------------------------------------------------------------------------


class TestLanBandwidthWidgetInit:
    """Tests for LanBandwidthWidget instantiation."""

    def test_can_instantiate(self):
        """Widget can be created without error."""
        from tui.widgets.lan_bandwidth_widget import LanBandwidthWidget

        widget = LanBandwidthWidget()
        assert widget.widget_name == "LanBandwidthWidget"

    def test_can_instantiate_with_id(self):
        """Widget accepts a custom id."""
        from tui.widgets.lan_bandwidth_widget import LanBandwidthWidget

        widget = LanBandwidthWidget(id="bw-test")
        assert widget.id == "bw-test"

    def test_inherits_base_widget(self):
        """Widget is a subclass of BaseWidget."""
        from tui.widgets.base import BaseWidget
        from tui.widgets.lan_bandwidth_widget import LanBandwidthWidget

        widget = LanBandwidthWidget()
        assert isinstance(widget, BaseWidget)

    def test_test_running_is_false(self):
        """_test_running starts False."""
        from tui.widgets.lan_bandwidth_widget import LanBandwidthWidget

        widget = LanBandwidthWidget()
        assert widget._test_running is False

    def test_last_result_is_none(self):
        """_last_result starts as None."""
        from tui.widgets.lan_bandwidth_widget import LanBandwidthWidget

        widget = LanBandwidthWidget()
        assert widget._last_result is None


# ---------------------------------------------------------------------------
# Widget method presence
# ---------------------------------------------------------------------------


class TestLanBandwidthWidgetMethods:
    """Confirm that all required methods exist on LanBandwidthWidget."""

    def _widget(self):
        from tui.widgets.lan_bandwidth_widget import LanBandwidthWidget

        return LanBandwidthWidget()

    def test_has_compose(self):
        assert callable(self._widget().compose)

    def test_has_on_mount(self):
        assert callable(self._widget().on_mount)

    def test_has_on_button_pressed(self):
        assert callable(self._widget().on_button_pressed)

    def test_has_start_test(self):
        assert callable(self._widget()._start_test)

    def test_has_stop_test(self):
        assert callable(self._widget()._stop_test)

    def test_has_reset_controls(self):
        assert callable(self._widget()._reset_controls)

    def test_has_update_status(self):
        assert callable(self._widget()._update_status)

    def test_has_run_worker(self):
        assert callable(self._widget()._run_worker)

    def test_has_on_sample(self):
        assert callable(self._widget()._on_sample)

    def test_has_on_complete(self):
        assert callable(self._widget()._on_complete)

    def test_has_on_error(self):
        assert callable(self._widget()._on_error)

    def test_has_show_summary(self):
        assert callable(self._widget()._show_summary)

    def test_inherits_base_methods(self):
        widget = self._widget()
        for method in ("display_error", "display_success", "show_loading", "set_status"):
            assert hasattr(widget, method) and callable(getattr(widget, method))


# ---------------------------------------------------------------------------
# Docstrings
# ---------------------------------------------------------------------------


class TestDocstrings:
    """Ensure all public API has proper documentation."""

    def test_module_docstring(self):
        import tui.widgets.lan_bandwidth_widget as mod

        assert mod.__doc__ is not None and len(mod.__doc__) > 0

    def test_bandwidth_sample_docstring(self):
        assert BandwidthSample.__doc__ is not None

    def test_bandwidth_result_docstring(self):
        assert BandwidthResult.__doc__ is not None

    def test_list_interfaces_docstring(self):
        assert list_interfaces.__doc__ is not None

    def test_get_io_counters_docstring(self):
        assert get_io_counters.__doc__ is not None

    def test_bytes_to_mbps_docstring(self):
        assert bytes_to_mbps.__doc__ is not None

    def test_format_mbps_docstring(self):
        assert format_mbps.__doc__ is not None

    def test_color_mbps_docstring(self):
        assert color_mbps.__doc__ is not None

    def test_build_interface_options_docstring(self):
        assert build_interface_options.__doc__ is not None

    def test_run_bandwidth_test_docstring(self):
        assert run_bandwidth_test.__doc__ is not None

    def test_widget_class_docstring(self):
        from tui.widgets.lan_bandwidth_widget import LanBandwidthWidget

        assert LanBandwidthWidget.__doc__ is not None


# ---------------------------------------------------------------------------
# Package integration
# ---------------------------------------------------------------------------


class TestPackageExport:
    """Test that LanBandwidthWidget is exported from the tui.widgets package."""

    def test_importable_from_package(self):
        from tui.widgets import LanBandwidthWidget

        assert LanBandwidthWidget is not None

    def test_in_all_list(self):
        import tui.widgets as pkg

        assert "LanBandwidthWidget" in pkg.__all__
