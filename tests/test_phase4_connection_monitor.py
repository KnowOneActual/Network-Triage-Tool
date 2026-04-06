"""Phase 4.5 Connection Monitor Widget Tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tui.widgets.connection_monitor_widget import (
    FILTER_ALL,
    FILTER_ESTABLISHED,
    FILTER_LISTEN,
    FILTER_TCP,
    FILTER_UDP,
    ConnectionEntry,
    apply_filter,
    apply_process_filter,
    color_status,
    format_connection_count,
    gather_connections,
)

# ---------------------------------------------------------------------------
# Helpers for building test data
# ---------------------------------------------------------------------------


def make_entry(
    protocol="TCP",
    local_addr="127.0.0.1",
    local_port=8080,
    remote_addr="93.184.216.34",
    remote_port=443,
    status="ESTABLISHED",
    pid=1234,
    process_name="python3",
) -> ConnectionEntry:
    """Build a ConnectionEntry with sensible defaults."""
    return ConnectionEntry(
        protocol=protocol,
        local_addr=local_addr,
        local_port=local_port,
        remote_addr=remote_addr,
        remote_port=remote_port,
        status=status,
        pid=pid,
        process_name=process_name,
    )


# ---------------------------------------------------------------------------
# ConnectionEntry data model
# ---------------------------------------------------------------------------


class TestConnectionEntry:
    """Tests for the ConnectionEntry dataclass."""

    def test_local_property_formats_correctly(self):
        """Test the local property formats addr:port."""
        entry = make_entry(local_addr="192.168.1.5", local_port=9000)
        assert entry.local == "192.168.1.5:9000"

    def test_remote_property_with_addr(self):
        """Test the remote property when a remote address is present."""
        entry = make_entry(remote_addr="8.8.8.8", remote_port=53)
        assert entry.remote == "8.8.8.8:53"

    def test_remote_property_empty_when_no_remote(self):
        """Test that remote returns '' when there is no remote address."""
        entry = make_entry(remote_addr="", remote_port=0, status="LISTEN")
        assert entry.remote == ""

    def test_pid_display_with_pid(self):
        """Test pid_display returns string of PID when set."""
        entry = make_entry(pid=42)
        assert entry.pid_display == "42"

    def test_pid_display_without_pid(self):
        """Test pid_display returns '-' when pid is None."""
        entry = make_entry(pid=None)
        assert entry.pid_display == "-"

    def test_protocol_stored_correctly(self):
        """Test protocol field is stored as provided."""
        tcp_entry = make_entry(protocol="TCP")
        udp_entry = make_entry(protocol="UDP")
        assert tcp_entry.protocol == "TCP"
        assert udp_entry.protocol == "UDP"

    def test_process_name_stored_correctly(self):
        """Test process_name is stored as provided."""
        entry = make_entry(process_name="nginx")
        assert entry.process_name == "nginx"

    def test_status_stored_correctly(self):
        """Test status field is stored as provided."""
        entry = make_entry(status="LISTEN")
        assert entry.status == "LISTEN"


# ---------------------------------------------------------------------------
# apply_filter
# ---------------------------------------------------------------------------


class TestApplyFilter:
    """Tests for the apply_filter() pure function."""

    def _sample_entries(self) -> list[ConnectionEntry]:
        return [
            make_entry(protocol="TCP", status="ESTABLISHED"),
            make_entry(protocol="TCP", status="LISTEN", remote_addr="", remote_port=0),
            make_entry(protocol="TCP", status="CLOSE_WAIT"),
            make_entry(protocol="UDP", status="NONE", remote_addr="", remote_port=0),
        ]

    def test_filter_all_returns_all(self):
        """FILTER_ALL should return every entry unchanged."""
        entries = self._sample_entries()
        result = apply_filter(entries, FILTER_ALL)
        assert len(result) == len(entries)

    def test_filter_tcp_only_returns_tcp(self):
        """FILTER_TCP should only return TCP entries."""
        entries = self._sample_entries()
        result = apply_filter(entries, FILTER_TCP)
        assert all(e.protocol == "TCP" for e in result)
        assert len(result) == 3

    def test_filter_udp_only_returns_udp(self):
        """FILTER_UDP should only return UDP entries."""
        entries = self._sample_entries()
        result = apply_filter(entries, FILTER_UDP)
        assert all(e.protocol == "UDP" for e in result)
        assert len(result) == 1

    def test_filter_established_returns_established(self):
        """FILTER_ESTABLISHED returns only ESTABLISHED connections."""
        entries = self._sample_entries()
        result = apply_filter(entries, FILTER_ESTABLISHED)
        assert all(e.status == "ESTABLISHED" for e in result)
        assert len(result) == 1

    def test_filter_listen_returns_listeners(self):
        """FILTER_LISTEN returns entries with LISTEN or NONE status and no remote."""
        entries = self._sample_entries()
        result = apply_filter(entries, FILTER_LISTEN)
        # Should include the LISTEN TCP and the NONE UDP (both have no remote)
        assert len(result) == 2

    def test_filter_close_wait_returns_matching(self):
        """Filtering by a custom status string returns matching entries."""
        entries = self._sample_entries()
        result = apply_filter(entries, "CLOSE_WAIT")
        assert all(e.status == "CLOSE_WAIT" for e in result)
        assert len(result) == 1

    def test_empty_list_returns_empty(self):
        """Filtering an empty list returns an empty list."""
        assert apply_filter([], FILTER_ALL) == []
        assert apply_filter([], FILTER_TCP) == []
        assert apply_filter([], FILTER_ESTABLISHED) == []

    def test_filter_preserves_order(self):
        """Filtering should preserve the original entry ordering."""
        entries = self._sample_entries()
        result = apply_filter(entries, FILTER_TCP)
        tcp_entries = [e for e in entries if e.protocol == "TCP"]
        assert result == tcp_entries

    def test_filter_listen_excludes_remote_connections(self):
        """LISTEN filter must not include established connections with remote addr."""
        entries = [
            make_entry(status="LISTEN", remote_addr="", remote_port=0),
            make_entry(status="LISTEN", remote_addr="10.0.0.1", remote_port=50000),  # has remote
        ]
        result = apply_filter(entries, FILTER_LISTEN)
        # Only the one without a remote address qualifies
        assert len(result) == 1
        assert result[0].remote_addr == ""


# ---------------------------------------------------------------------------
# apply_process_filter
# ---------------------------------------------------------------------------


class TestApplyProcessFilter:
    """Tests for the apply_process_filter() pure function."""

    def _entries(self) -> list[ConnectionEntry]:
        return [
            make_entry(process_name="python3", local_addr="127.0.0.1"),
            make_entry(process_name="nginx", local_addr="0.0.0.0"),  # noqa: S104
            make_entry(process_name="sshd", local_addr="0.0.0.0"),  # noqa: S104
            make_entry(process_name="Python", local_addr="192.168.1.100"),
        ]

    def test_empty_search_returns_all(self):
        """An empty search string returns all entries."""
        entries = self._entries()
        result = apply_process_filter(entries, "")
        assert result == entries

    def test_whitespace_search_returns_all(self):
        """A whitespace-only search string returns all entries."""
        entries = self._entries()
        assert apply_process_filter(entries, "   ") == entries

    def test_match_by_process_name(self):
        """Matching by process name substring works."""
        entries = self._entries()
        result = apply_process_filter(entries, "nginx")
        assert len(result) == 1
        assert result[0].process_name == "nginx"

    def test_match_is_case_insensitive(self):
        """Process name match is case-insensitive."""
        entries = self._entries()
        result = apply_process_filter(entries, "PYTHON")
        # Matches 'python3' and 'Python'
        assert len(result) == 2

    def test_match_by_local_addr(self):
        """Matching by local address substring works."""
        entries = self._entries()
        result = apply_process_filter(entries, "192.168")
        assert len(result) == 1
        assert result[0].local_addr == "192.168.1.100"

    def test_no_match_returns_empty(self):
        """A search with no matches returns an empty list."""
        entries = self._entries()
        result = apply_process_filter(entries, "xyz_nonexistent")
        assert result == []

    def test_empty_list_returns_empty(self):
        """An empty entry list returns empty regardless of search."""
        assert apply_process_filter([], "nginx") == []


# ---------------------------------------------------------------------------
# color_status
# ---------------------------------------------------------------------------


class TestColorStatus:
    """Tests for the color_status() helper."""

    def test_established_is_green(self):
        """ESTABLISHED connections should use green markup."""
        result = color_status("ESTABLISHED")
        assert "[green]" in result
        assert "ESTABLISHED" in result

    def test_listen_is_yellow(self):
        """LISTEN connections should use yellow markup."""
        result = color_status("LISTEN")
        assert "[yellow]" in result

    def test_close_wait_is_red(self):
        """CLOSE_WAIT should be marked red."""
        result = color_status("CLOSE_WAIT")
        assert "[red]" in result

    def test_time_wait_uses_dim(self):
        """TIME_WAIT should use bright_black (dim) colour."""
        result = color_status("TIME_WAIT")
        assert "[bright_black]" in result

    def test_unknown_status_uses_white(self):
        """An unrecognised status defaults to white."""
        result = color_status("UNKNOWN_STATE")
        assert "[white]" in result

    def test_markup_is_closed(self):
        """The returned markup should have a matching closing tag."""
        result = color_status("ESTABLISHED")
        assert "[/green]" in result

    def test_status_text_in_result(self):
        """The status string itself should appear in the output."""
        for status in ("ESTABLISHED", "LISTEN", "SYN_SENT", "NONE"):
            assert status in color_status(status)


# ---------------------------------------------------------------------------
# format_connection_count
# ---------------------------------------------------------------------------


class TestFormatConnectionCount:
    """Tests for the format_connection_count() helper."""

    def test_no_filter_singular(self):
        """Single connection with no filter shows singular form."""
        result = format_connection_count(1, 1)
        assert "1 connection" in result
        assert "connections" not in result

    def test_no_filter_plural(self):
        """Multiple connections with no filter shows plural form."""
        result = format_connection_count(5, 5)
        assert "5 connections" in result
        assert "filtered" not in result

    def test_filtered_shows_ratio(self):
        """When filter is applied, shows 'X of Y' format."""
        result = format_connection_count(10, 3)
        assert "3 of 10" in result
        assert "filtered" in result

    def test_zero_connections(self):
        """Zero connections is handled gracefully."""
        result = format_connection_count(0, 0)
        assert "0" in result

    def test_all_filtered_out(self):
        """When all connections are filtered out, shows 0 of N."""
        result = format_connection_count(5, 0)
        assert "0 of 5" in result


# ---------------------------------------------------------------------------
# gather_connections
# ---------------------------------------------------------------------------


class TestGatherConnections:
    """Tests for the gather_connections() function with mocked psutil."""

    def _make_mock_conn(
        self,
        kind="SOCK_STREAM",
        laddr=("127.0.0.1", 8080),
        raddr=("93.184.216.34", 443),
        status="ESTABLISHED",
        pid=100,
    ):
        """Create a mock psutil connection namedtuple."""
        conn = MagicMock()
        conn.type = MagicMock()
        conn.type.name = kind
        conn.laddr = MagicMock()
        conn.laddr.ip, conn.laddr.port = laddr
        conn.raddr = None if raddr == () else MagicMock()
        if raddr:
            conn.raddr.ip, conn.raddr.port = raddr
        conn.status = status
        conn.pid = pid
        return conn

    def test_returns_list(self):
        """gather_connections returns a list."""
        with patch("tui.widgets.connection_monitor_widget.psutil.net_connections", return_value=[]):
            result = gather_connections()
        assert isinstance(result, list)

    def test_empty_when_no_connections(self):
        """Returns empty list when psutil reports no connections."""
        with patch("tui.widgets.connection_monitor_widget.psutil.net_connections", return_value=[]):
            result = gather_connections()
        assert result == []

    def test_tcp_connection_parsed(self):
        """A SOCK_STREAM connection is parsed as TCP."""
        mock_conn = self._make_mock_conn(kind="SOCK_STREAM")
        with (
            patch("tui.widgets.connection_monitor_widget.psutil.net_connections", return_value=[mock_conn]),
            patch("tui.widgets.connection_monitor_widget.psutil.Process") as mock_proc,
        ):
            mock_proc.return_value.name.return_value = "python3"
            result = gather_connections()
        assert len(result) == 1
        assert result[0].protocol == "TCP"

    def test_udp_connection_parsed(self):
        """A SOCK_DGRAM connection is parsed as UDP."""
        mock_conn = self._make_mock_conn(kind="SOCK_DGRAM", raddr=(), status="NONE")
        mock_conn.raddr = None
        with (
            patch("tui.widgets.connection_monitor_widget.psutil.net_connections", return_value=[mock_conn]),
            patch("tui.widgets.connection_monitor_widget.psutil.Process") as mock_proc,
        ):
            mock_proc.return_value.name.return_value = "udpapp"
            result = gather_connections()
        assert len(result) == 1
        assert result[0].protocol == "UDP"

    def test_addresses_parsed_correctly(self):
        """Local and remote addresses are extracted correctly."""
        mock_conn = self._make_mock_conn(
            laddr=("0.0.0.0", 22),  # noqa: S104
            raddr=("10.0.0.5", 54321),
            status="ESTABLISHED",
        )
        with (
            patch("tui.widgets.connection_monitor_widget.psutil.net_connections", return_value=[mock_conn]),
            patch("tui.widgets.connection_monitor_widget.psutil.Process") as mock_proc,
        ):
            mock_proc.return_value.name.return_value = "sshd"
            result = gather_connections()
        assert result[0].local_addr == "0.0.0.0"  # noqa: S104
        assert result[0].local_port == 22
        assert result[0].remote_addr == "10.0.0.5"
        assert result[0].remote_port == 54321

    def test_status_extracted(self):
        """Connection status is extracted from psutil."""
        mock_conn = self._make_mock_conn(status="LISTEN")
        with (
            patch("tui.widgets.connection_monitor_widget.psutil.net_connections", return_value=[mock_conn]),
            patch("tui.widgets.connection_monitor_widget.psutil.Process") as mock_proc,
        ):
            mock_proc.return_value.name.return_value = "apache"
            result = gather_connections()
        assert result[0].status == "LISTEN"

    def test_access_denied_returns_empty(self):
        """AccessDenied from psutil returns an empty list, not an exception."""
        import psutil as _psutil

        with patch(
            "tui.widgets.connection_monitor_widget.psutil.net_connections",
            side_effect=_psutil.AccessDenied(pid=0),
        ):
            result = gather_connections()
        assert result == []

    def test_unknown_exception_returns_empty(self):
        """An unexpected exception returns an empty list."""
        with patch(
            "tui.widgets.connection_monitor_widget.psutil.net_connections",
            side_effect=RuntimeError("unexpected"),
        ):
            result = gather_connections()
        assert result == []

    def test_no_such_process_handled(self):
        """NoSuchProcess on Process.name() is handled gracefully."""
        import psutil as _psutil

        mock_conn = self._make_mock_conn(pid=9999)
        with (
            patch("tui.widgets.connection_monitor_widget.psutil.net_connections", return_value=[mock_conn]),
            patch("tui.widgets.connection_monitor_widget.psutil.Process") as mock_proc,
        ):
            mock_proc.return_value.name.side_effect = _psutil.NoSuchProcess(pid=9999)
            result = gather_connections()
        # Should still return the entry, just with '<unknown>' process name
        assert len(result) == 1
        assert result[0].process_name == "<unknown>"

    def test_pid_none_handled(self):
        """A None PID does not cause an error."""
        mock_conn = self._make_mock_conn(pid=None)
        with patch("tui.widgets.connection_monitor_widget.psutil.net_connections", return_value=[mock_conn]):
            result = gather_connections()
        assert len(result) == 1
        assert result[0].pid is None
        assert result[0].process_name == ""


# ---------------------------------------------------------------------------
# Widget initialization
# ---------------------------------------------------------------------------


class TestConnectionMonitorWidgetInitialization:
    """Tests for ConnectionMonitorWidget initialization."""

    def test_widget_can_be_instantiated(self):
        """Widget can be created without error."""
        from tui.widgets.connection_monitor_widget import ConnectionMonitorWidget

        widget = ConnectionMonitorWidget()
        assert widget.widget_name == "ConnectionMonitorWidget"

    def test_widget_with_id(self):
        """Widget can be created with a custom id."""
        from tui.widgets.connection_monitor_widget import ConnectionMonitorWidget

        widget = ConnectionMonitorWidget(id="test_conn_mon")
        assert widget.id == "test_conn_mon"

    def test_inherits_from_base_widget(self):
        """Widget inherits from BaseWidget."""
        from tui.widgets.base import BaseWidget
        from tui.widgets.connection_monitor_widget import ConnectionMonitorWidget

        widget = ConnectionMonitorWidget()
        assert isinstance(widget, BaseWidget)

    def test_refresh_in_progress_false_by_default(self):
        """_refresh_in_progress flag starts False."""
        from tui.widgets.connection_monitor_widget import ConnectionMonitorWidget

        widget = ConnectionMonitorWidget()
        assert widget._refresh_in_progress is False

    def test_auto_refresh_disabled_by_default(self):
        """Auto-refresh is off by default."""
        from tui.widgets.connection_monitor_widget import ConnectionMonitorWidget

        widget = ConnectionMonitorWidget()
        assert widget._auto_refresh_enabled is False

    def test_all_connections_empty_on_init(self):
        """_all_connections starts as an empty list."""
        from tui.widgets.connection_monitor_widget import ConnectionMonitorWidget

        widget = ConnectionMonitorWidget()
        assert widget._all_connections == []


# ---------------------------------------------------------------------------
# Widget method presence
# ---------------------------------------------------------------------------


class TestConnectionMonitorWidgetMethods:
    """Tests confirming required methods exist on the widget."""

    def _widget(self):
        from tui.widgets.connection_monitor_widget import ConnectionMonitorWidget

        return ConnectionMonitorWidget()

    def test_has_compose(self):
        assert callable(self._widget().compose)

    def test_has_on_mount(self):
        assert callable(self._widget().on_mount)

    def test_has_on_button_pressed(self):
        assert callable(self._widget().on_button_pressed)

    def test_has_on_select_changed(self):
        assert callable(self._widget().on_select_changed)

    def test_has_on_input_changed(self):
        assert callable(self._widget().on_input_changed)

    def test_has_do_refresh(self):
        assert callable(self._widget()._do_refresh)

    def test_has_toggle_auto_refresh(self):
        assert callable(self._widget()._toggle_auto_refresh)

    def test_has_apply_current_filter(self):
        assert callable(self._widget()._apply_current_filter)

    def test_has_required_base_methods(self):
        widget = self._widget()
        for method in ("display_error", "display_success", "show_loading", "set_status"):
            assert hasattr(widget, method) and callable(getattr(widget, method))


# ---------------------------------------------------------------------------
# Docstrings
# ---------------------------------------------------------------------------


class TestDocstrings:
    """Ensure public API has proper documentation."""

    def test_module_has_docstring(self):
        import tui.widgets.connection_monitor_widget as mod

        assert mod.__doc__ is not None and len(mod.__doc__) > 0

    def test_connection_entry_has_docstring(self):
        assert ConnectionEntry.__doc__ is not None

    def test_gather_connections_has_docstring(self):
        assert gather_connections.__doc__ is not None

    def test_apply_filter_has_docstring(self):
        assert apply_filter.__doc__ is not None

    def test_apply_process_filter_has_docstring(self):
        assert apply_process_filter.__doc__ is not None

    def test_color_status_has_docstring(self):
        assert color_status.__doc__ is not None

    def test_format_connection_count_has_docstring(self):
        assert format_connection_count.__doc__ is not None

    def test_widget_class_has_docstring(self):
        from tui.widgets.connection_monitor_widget import ConnectionMonitorWidget

        assert ConnectionMonitorWidget.__doc__ is not None


# ---------------------------------------------------------------------------
# Integration — package export
# ---------------------------------------------------------------------------


class TestPackageExport:
    """Test that ConnectionMonitorWidget is exported from the tui.widgets package."""

    def test_importable_from_package(self):
        from tui.widgets import ConnectionMonitorWidget

        assert ConnectionMonitorWidget is not None

    def test_in_all_list(self):
        import tui.widgets as pkg

        assert "ConnectionMonitorWidget" in pkg.__all__
