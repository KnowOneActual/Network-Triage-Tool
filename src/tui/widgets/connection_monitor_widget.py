"""Connection Monitor Widget for Phase 4.5.

Displays active TCP/UDP socket connections with associated process information.
Uses psutil for cross-platform socket enumeration, running entirely on a
background thread so the UI never blocks.
"""

import logging
from dataclasses import dataclass
from typing import Any

import psutil
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Label, Select

from .base import BaseWidget

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ConnectionEntry:
    """Represents a single active network connection."""

    protocol: str
    local_addr: str
    local_port: int
    remote_addr: str
    remote_port: int
    status: str
    pid: int | None
    process_name: str

    @property
    def local(self) -> str:
        """Human-readable local address:port."""
        return f"{self.local_addr}:{self.local_port}"

    @property
    def remote(self) -> str:
        """Human-readable remote address:port (empty for listeners)."""
        if self.remote_addr:
            return f"{self.remote_addr}:{self.remote_port}"
        return ""

    @property
    def pid_display(self) -> str:
        """PID as a string, or '-' when unknown."""
        return str(self.pid) if self.pid is not None else "-"


# ---------------------------------------------------------------------------
# Filter constants
# ---------------------------------------------------------------------------

FILTER_ALL = "all"
FILTER_ESTABLISHED = "ESTABLISHED"
FILTER_LISTEN = "LISTEN"
FILTER_TCP = "tcp"
FILTER_UDP = "udp"

FILTER_OPTIONS: list[tuple[str, str]] = [
    ("All Connections", FILTER_ALL),
    ("ESTABLISHED", FILTER_ESTABLISHED),
    ("LISTEN / Bound", FILTER_LISTEN),
    ("TCP only", FILTER_TCP),
    ("UDP only", FILTER_UDP),
]

# Rich-markup colour for each connection status
STATUS_COLORS: dict[str, str] = {
    "ESTABLISHED": "green",
    "LISTEN": "yellow",
    "SYN_SENT": "cyan",
    "SYN_RECV": "cyan",
    "CLOSE_WAIT": "red",
    "FIN_WAIT1": "magenta",
    "FIN_WAIT2": "magenta",
    "TIME_WAIT": "bright_black",
    "CLOSING": "red",
    "LAST_ACK": "magenta",
    "NONE": "bright_black",
}


# ---------------------------------------------------------------------------
# Pure helpers (no app/widget context — easy to unit-test)
# ---------------------------------------------------------------------------


def gather_connections() -> list[ConnectionEntry]:
    """Collect active network connections via psutil.

    Returns:
        List of ConnectionEntry objects for all TCP and UDP sockets.
        Returns an empty list if psutil is unavailable or access is denied.

    """
    entries: list[ConnectionEntry] = []
    try:
        # net_connections replaces the deprecated psutil.net_connections
        # in newer psutil versions; fall back gracefully.
        try:
            conns = psutil.net_connections(kind="inet")
        except AttributeError:  # pragma: no cover
            conns = psutil.net_connections()

        # Build a pid→name cache to avoid per-connection Process() calls
        pid_cache: dict[int, str] = {}

        for c in conns:
            pid = c.pid
            proc_name = ""
            if pid is not None:
                if pid not in pid_cache:
                    try:
                        proc_name = psutil.Process(pid).name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        proc_name = "<unknown>"
                    pid_cache[pid] = proc_name
                else:
                    proc_name = pid_cache[pid]

            # Determine protocol string
            if c.type.name == "SOCK_STREAM":
                proto = "TCP"
            elif c.type.name == "SOCK_DGRAM":
                proto = "UDP"
            else:
                proto = c.type.name

            laddr, lport = (c.laddr.ip, c.laddr.port) if c.laddr else ("", 0)
            raddr, rport = (c.raddr.ip, c.raddr.port) if c.raddr else ("", 0)
            status = c.status or "NONE"

            entries.append(
                ConnectionEntry(
                    protocol=proto,
                    local_addr=laddr,
                    local_port=lport,
                    remote_addr=raddr,
                    remote_port=rport,
                    status=status,
                    pid=pid,
                    process_name=proc_name,
                ),
            )
    except psutil.AccessDenied:
        logger.warning("Access denied when reading network connections — try running with elevated privileges")
    except Exception as e:
        logger.error(f"Error gathering connections: {e}", exc_info=True)

    return entries


def apply_filter(entries: list[ConnectionEntry], filter_value: str) -> list[ConnectionEntry]:
    """Filter a list of ConnectionEntry objects by the given filter."""
    match filter_value:
        case typeof_filter if typeof_filter == FILTER_ALL:
            return entries
        case typeof_filter if typeof_filter == FILTER_TCP:
            return [e for e in entries if e.protocol == "TCP"]
        case typeof_filter if typeof_filter == FILTER_UDP:
            return [e for e in entries if e.protocol == "UDP"]
        case typeof_filter if typeof_filter == FILTER_ESTABLISHED:
            return [e for e in entries if e.status == "ESTABLISHED"]
        case typeof_filter if typeof_filter == FILTER_LISTEN:
            # "LISTEN" covers TCP listeners; UDP bound sockets have no state
            return [e for e in entries if e.status in ("LISTEN", "NONE") and not e.remote_addr]
        case _:
            # Custom status match (e.g. "CLOSE_WAIT")
            return [e for e in entries if e.status == filter_value]


def apply_process_filter(entries: list[ConnectionEntry], search: str) -> list[ConnectionEntry]:
    """Filter connections by process name substring.

    Args:
        entries: List of connections.
        search: Substring to search for in process_name (case-insensitive).
                An empty string returns all entries unchanged.

    Returns:
        Filtered list.

    """
    if not search.strip():
        return entries
    needle = search.strip().lower()
    return [e for e in entries if needle in e.process_name.lower() or needle in e.local_addr.lower()]


def color_status(status: str) -> str:
    """Return a Rich-markup coloured status string.

    Args:
        status: Connection status string (e.g. 'ESTABLISHED').

    Returns:
        Rich markup string.

    """
    color = STATUS_COLORS.get(status, "white")
    return f"[{color}]{status}[/{color}]"


def format_connection_count(total: int, shown: int) -> str:
    """Build a human-readable connection count message.

    Args:
        total: Total connections before filter.
        shown: Connections after filter.

    Returns:
        Summary string.

    """
    if total == shown:
        return f"{total} connection{'s' if total != 1 else ''}"
    return f"{shown} of {total} connection{'s' if total != 1 else ''} (filtered)"


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class ConnectionMonitorWidget(BaseWidget):
    """Connection Monitor Widget — live TCP/UDP socket monitor with process info.

    Displays all active network connections with local/remote addresses,
    connection status, and the owning process (name + PID). Supports filtering
    by protocol, status, and process name. Refreshes on demand or automatically
    every 10 seconds when auto-refresh is enabled.
    """

    # Refresh interval in seconds
    AUTO_REFRESH_INTERVAL: float = 10.0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.widget_name = "ConnectionMonitorWidget"
        self._refresh_in_progress = False
        self._auto_refresh_enabled = False
        self._all_connections: list[ConnectionEntry] = []
        self._auto_refresh_timer = None

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        """Compose the Connection Monitor UI."""
        yield Label("[bold]Connection Monitor[/bold]", id="conn-mon-title")

        with Vertical(id="conn-mon-controls"):
            with Horizontal(id="conn-mon-top-bar"):
                yield Button("🔄 Refresh", id="refresh-btn", variant="primary")
                yield Button("⏱ Auto-Refresh: OFF", id="auto-btn", variant="default")

                yield Label("Filter:", id="filter-label")
                yield Select(
                    options=FILTER_OPTIONS,
                    allow_blank=False,
                    value=FILTER_ALL,
                    id="filter-select",
                )

            with Horizontal(id="conn-mon-search-bar"):
                yield Label("Search process / address:", id="search-label")
                yield Input(
                    id="search-input",
                    placeholder="e.g. python, 8.8.8.8 …",
                    tooltip="Filter rows by process name or local address",
                )
                yield Button("Clear", id="clear-search-btn", variant="default")

        yield Label("", id="conn-mon-count")
        yield DataTable(id="connections-table")
        yield Label("", id="conn-mon-status")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        """Configure the DataTable and trigger the first refresh."""
        table = self.query_one("#connections-table", DataTable)
        table.add_columns("Proto", "Local Address", "Remote Address", "Status", "PID", "Process")
        table.cursor_type = "row"
        self._do_refresh()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id
        if btn_id == "refresh-btn":
            self._do_refresh()
        elif btn_id == "auto-btn":
            self._toggle_auto_refresh()
        elif btn_id == "clear-search-btn":
            self.query_one("#search-input", Input).value = ""
            self._apply_current_filter()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Re-apply filter when the dropdown changes."""
        if event.select.id == "filter-select":
            self._apply_current_filter()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Re-apply filter as the search term changes."""
        if event.input.id == "search-input":
            self._apply_current_filter()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Copy the remote address to clipboard on row click."""
        table = self.query_one("#connections-table", DataTable)
        try:
            row_data = table.get_row(event.row_key)
            # row_data[2] is the remote address column
            remote = str(row_data[2]) if row_data[2] else ""
            if remote and remote != "–":
                self.app.copy_to_clipboard(remote)
                self.app.notify(f"Copied: {remote}", title="Clipboard", severity="information", timeout=2)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public control methods
    # ------------------------------------------------------------------

    def _do_refresh(self) -> None:
        """Trigger a background connection refresh if not already running."""
        if self._refresh_in_progress:
            self.set_status("Refresh already in progress…")
            return
        self._refresh_in_progress = True
        self.show_loading("Scanning connections…")
        self.set_status("Scanning…")
        self._refresh_worker()

    def _toggle_auto_refresh(self) -> None:
        """Enable or disable the auto-refresh timer."""
        self._auto_refresh_enabled = not self._auto_refresh_enabled
        btn = self.query_one("#auto-btn", Button)
        if self._auto_refresh_enabled:
            btn.label = "⏱ Auto-Refresh: ON"
            btn.variant = "success"
            self._auto_refresh_timer = self.set_interval(self.AUTO_REFRESH_INTERVAL, self._do_refresh)
        else:
            btn.label = "⏱ Auto-Refresh: OFF"
            btn.variant = "default"
            if self._auto_refresh_timer is not None:
                self._auto_refresh_timer.stop()
                self._auto_refresh_timer = None

    def _apply_current_filter(self) -> None:
        """Re-render the table using the current filter and search values."""
        filter_val = str(self.query_one("#filter-select", Select).value)
        search_val = self.query_one("#search-input", Input).value
        filtered = apply_filter(self._all_connections, filter_val)
        filtered = apply_process_filter(filtered, search_val)
        self._populate_table(filtered)
        count_label = format_connection_count(len(self._all_connections), len(filtered))
        self.query_one("#conn-mon-count", Label).update(count_label)

    # ------------------------------------------------------------------
    # Background worker
    # ------------------------------------------------------------------

    @work(thread=True)
    def _refresh_worker(self) -> None:
        """Gather connections on a background thread then update the UI."""
        try:
            connections = gather_connections()
            self.app.call_from_thread(self._on_refresh_complete, connections)
        except Exception as e:
            logger.error(f"Connection monitor refresh error: {e}", exc_info=True)
            self.app.call_from_thread(self._on_refresh_error, str(e))

    # ------------------------------------------------------------------
    # UI-thread callbacks
    # ------------------------------------------------------------------

    def _on_refresh_complete(self, connections: list[ConnectionEntry]) -> None:
        """Receive fresh connections and update the display (UI thread)."""
        self._refresh_in_progress = False
        self._all_connections = connections
        self._apply_current_filter()
        self.display_success(f"Found {len(connections)} active connections")
        self.set_status(f"✓ {len(connections)} connections")

    def _on_refresh_error(self, error_msg: str) -> None:
        """Handle worker errors on the UI thread."""
        self._refresh_in_progress = False
        self.display_error(f"Refresh failed: {error_msg}")
        self.set_status("Error")

    def _populate_table(self, connections: list[ConnectionEntry]) -> None:
        """Populate the DataTable with the given connection list (UI thread).

        Args:
            connections: Filtered list of ConnectionEntry objects to display.

        """
        table = self.query_one("#connections-table", DataTable)
        table.clear()
        for conn in connections:
            table.add_row(
                conn.protocol,
                conn.local,
                conn.remote or "–",
                color_status(conn.status),
                conn.pid_display,
                conn.process_name or "–",
            )
