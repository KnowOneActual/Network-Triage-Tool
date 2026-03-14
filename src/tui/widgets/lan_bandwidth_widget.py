"""LAN Bandwidth Tester Widget for Phase 4.6.

Measures live network interface throughput by sampling psutil.net_io_counters()
over a user-configurable interval. No external server or iperf3 binary is
required — this is a pure psutil-based, stdlib-only implementation.

Features:
- Interface selector (all detected adapters)
- Live throughput sampling (RX / TX Mbps per tick)
- Configurable sample duration (5 / 10 / 30 / 60 seconds)
- Peak RX / TX tracking
- Running average RX / TX
- A scrollable, timestamped results log
- Auto-stop on completion with a clean summary
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime

import psutil
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Select, Static

from .base import BaseWidget

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BYTES_PER_MBIT = 125_000  # 1 Mbit/s = 125,000 bytes/s

DURATION_OPTIONS: list[tuple[str, str]] = [
    ("5 seconds", "5"),
    ("10 seconds", "10"),
    ("30 seconds", "30"),
    ("60 seconds", "60"),
]

SAMPLE_INTERVAL: float = 1.0  # seconds between psutil polls


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class BandwidthSample:
    """A single throughput measurement taken at one point in time."""

    timestamp: str
    rx_mbps: float
    tx_mbps: float
    elapsed: float  # seconds since test start


@dataclass
class BandwidthResult:
    """Aggregate result of a completed bandwidth test."""

    interface: str
    duration: int
    samples: list[BandwidthSample] = field(default_factory=list)

    @property
    def avg_rx_mbps(self) -> float:
        """Average receive throughput in Mbit/s."""
        if not self.samples:
            return 0.0
        return sum(s.rx_mbps for s in self.samples) / len(self.samples)

    @property
    def avg_tx_mbps(self) -> float:
        """Average transmit throughput in Mbit/s."""
        if not self.samples:
            return 0.0
        return sum(s.tx_mbps for s in self.samples) / len(self.samples)

    @property
    def peak_rx_mbps(self) -> float:
        """Peak receive throughput in Mbit/s."""
        if not self.samples:
            return 0.0
        return max(s.rx_mbps for s in self.samples)

    @property
    def peak_tx_mbps(self) -> float:
        """Peak transmit throughput in Mbit/s."""
        if not self.samples:
            return 0.0
        return max(s.tx_mbps for s in self.samples)

    @property
    def sample_count(self) -> int:
        """Number of valid samples recorded."""
        return len(self.samples)


# ---------------------------------------------------------------------------
# Pure helpers (no widget context — easily unit-tested)
# ---------------------------------------------------------------------------


def list_interfaces() -> list[str]:
    """Return names of all network interfaces reported by psutil.

    Returns:
        Sorted list of interface name strings.
    """
    try:
        return sorted(psutil.net_if_stats().keys())
    except Exception:  # pragma: no cover — OS-level failure
        return []


def get_io_counters(interface: str) -> tuple[int, int] | None:
    """Read current cumulative bytes_recv / bytes_sent for *interface*.

    Args:
        interface: Interface name (e.g. 'en0', 'eth0', or 'all').
                   Pass 'all' to aggregate across all adapters.

    Returns:
        Tuple of (bytes_recv, bytes_sent), or None on failure.
    """
    try:
        if interface == "all":
            counters = psutil.net_io_counters(pernic=False)
            if counters is None:
                return None
            return counters.bytes_recv, counters.bytes_sent
        per_nic = psutil.net_io_counters(pernic=True)
        if interface not in per_nic:
            return None
        c = per_nic[interface]
        return c.bytes_recv, c.bytes_sent
    except Exception as exc:
        logger.warning("Could not read IO counters for %s: %s", interface, exc)
        return None


def bytes_to_mbps(byte_delta: int, elapsed_seconds: float) -> float:
    """Convert a byte delta over a time window to Mbit/s.

    Args:
        byte_delta: Number of bytes transferred in the window.
        elapsed_seconds: Length of the measurement window in seconds.

    Returns:
        Throughput in Mbit/s, or 0.0 if elapsed_seconds is zero.
    """
    if elapsed_seconds <= 0:
        return 0.0
    return (byte_delta / elapsed_seconds) / BYTES_PER_MBIT


def format_mbps(value: float) -> str:
    """Format a Mbit/s value for display.

    Args:
        value: Throughput in Mbit/s.

    Returns:
        Human-readable string such as '12.34 Mbps' or '1.20 Gbps'.
    """
    if value >= 1000:
        return f"{value / 1000:.2f} Gbps"
    return f"{value:.2f} Mbps"


def color_mbps(value: float) -> str:
    """Return Rich-markup coloured throughput string.

    Colour bands:
    - green  : ≥ 100 Mbps
    - yellow : ≥ 10 Mbps
    - red    : < 10 Mbps

    Args:
        value: Throughput in Mbit/s.

    Returns:
        Rich markup string with colour tags.
    """
    text = format_mbps(value)
    if value >= 100:
        return f"[green]{text}[/green]"
    if value >= 10:
        return f"[yellow]{text}[/yellow]"
    return f"[red]{text}[/red]"


def build_interface_options() -> list[tuple[str, str]]:
    """Build a Select-compatible option list from available network interfaces.

    Returns:
        List of (label, value) tuples including an 'All Interfaces' aggregate
        option as the first entry.
    """
    ifaces = list_interfaces()
    options: list[tuple[str, str]] = [("All Interfaces", "all")]
    for iface in ifaces:
        options.append((iface, iface))
    return options


def run_bandwidth_test(interface: str, duration: int) -> BandwidthResult:
    """Measure network throughput by polling psutil over *duration* seconds.

    This is a **blocking** function — always call it from a background thread.

    The function polls the OS IO counters every SAMPLE_INTERVAL seconds.
    Each tick computes the delta since the previous tick and converts to Mbps.

    Args:
        interface: Interface name to monitor, or 'all' for aggregate.
        duration: Total test duration in seconds.

    Returns:
        BandwidthResult containing all samples.
    """
    result = BandwidthResult(interface=interface, duration=duration)

    baseline = get_io_counters(interface)
    if baseline is None:
        logger.error("Cannot read counters for interface '%s'", interface)
        return result

    prev_rx, prev_tx = baseline
    prev_time = time.monotonic()
    start_time = prev_time

    while True:
        time.sleep(SAMPLE_INTERVAL)
        now = time.monotonic()
        elapsed_since_start = now - start_time

        counters = get_io_counters(interface)
        if counters is None:
            break

        curr_rx, curr_tx = counters
        window = now - prev_time

        rx_mbps = bytes_to_mbps(max(0, curr_rx - prev_rx), window)
        tx_mbps = bytes_to_mbps(max(0, curr_tx - prev_tx), window)

        sample = BandwidthSample(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            rx_mbps=rx_mbps,
            tx_mbps=tx_mbps,
            elapsed=elapsed_since_start,
        )
        result.samples.append(sample)

        prev_rx, prev_tx = curr_rx, curr_tx
        prev_time = now

        if elapsed_since_start >= duration:
            break

    return result


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class LanBandwidthWidget(BaseWidget):
    """LAN Bandwidth Tester Widget — live network I/O throughput monitor.

    Measures real-time RX / TX throughput by sampling psutil counters every
    second over a user-configured duration. Results are displayed in a
    timestamped DataTable with aggregate stats shown below.

    No external tools (iperf3, netcat, etc.) are required.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget_name = "LanBandwidthWidget"
        self._test_running = False
        self._last_result: BandwidthResult | None = None

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        """Compose the LAN Bandwidth Tester UI."""
        yield Label("[bold]LAN Bandwidth Tester[/bold]", id="bw-title")

        with Vertical(id="bw-controls"):
            with Horizontal(id="bw-top-bar"):
                yield Label("Interface:", id="bw-iface-label")
                yield Select(
                    options=build_interface_options(),
                    allow_blank=False,
                    value="all",
                    id="bw-iface-select",
                )

                yield Label("Duration:", id="bw-dur-label")
                yield Select(
                    options=DURATION_OPTIONS,
                    allow_blank=False,
                    value="10",
                    id="bw-dur-select",
                )

                yield Button("▶ Start Test", id="bw-start-btn", variant="success")
                yield Button("⏹ Stop", id="bw-stop-btn", variant="error", disabled=True)

        yield Label("", id="bw-status-label")
        yield DataTable(id="bw-table")

        with Horizontal(id="bw-summary"):
            yield Static("", id="bw-summary-rx")
            yield Static("", id="bw-summary-tx")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        """Configure DataTable columns on mount."""
        table = self.query_one("#bw-table", DataTable)
        table.add_columns("Time", "Elapsed (s)", "↓ RX", "↑ TX")
        table.cursor_type = "none"

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Start / Stop button presses."""
        btn_id = event.button.id
        if btn_id == "bw-start-btn":
            self._start_test()
        elif btn_id == "bw-stop-btn":
            self._stop_test()

    # ------------------------------------------------------------------
    # Control methods
    # ------------------------------------------------------------------

    def _start_test(self) -> None:
        """Validate inputs and launch the background bandwidth worker."""
        if self._test_running:
            return

        iface = str(self.query_one("#bw-iface-select", Select).value)
        duration_str = str(self.query_one("#bw-dur-select", Select).value)

        try:
            duration = int(duration_str)
        except ValueError:
            self.display_error("Invalid duration value.")
            return

        # Reset table and summary
        self.query_one("#bw-table", DataTable).clear()
        self.query_one("#bw-summary-rx", Static).update("")
        self.query_one("#bw-summary-tx", Static).update("")
        self._last_result = None

        # Update UI state
        self._test_running = True
        self.query_one("#bw-start-btn", Button).disabled = True
        self.query_one("#bw-stop-btn", Button).disabled = False
        self.query_one("#bw-iface-select", Select).disabled = True
        self.query_one("#bw-dur-select", Select).disabled = True
        self.show_loading(f"Measuring {iface} for {duration}s…")
        self._update_status(f"⏱ Running — 0/{duration}s")

        self._run_worker(iface, duration)

    def _stop_test(self) -> None:
        """Cancel any in-flight test (best-effort via worker cancellation)."""
        self.workers.cancel_all()
        self._test_running = False
        self._reset_controls()
        self._update_status("⛔ Stopped by user.")

    def _reset_controls(self) -> None:
        """Re-enable controls after a test finishes or is stopped."""
        self.query_one("#bw-start-btn", Button).disabled = False
        self.query_one("#bw-stop-btn", Button).disabled = True
        self.query_one("#bw-iface-select", Select).disabled = False
        self.query_one("#bw-dur-select", Select).disabled = False

    def _update_status(self, text: str) -> None:
        """Update the status label."""
        self.query_one("#bw-status-label", Label).update(text)

    # ------------------------------------------------------------------
    # Background worker
    # ------------------------------------------------------------------

    @work(thread=True)
    def _run_worker(self, interface: str, duration: int) -> None:
        """Run the blocking bandwidth test on a background thread.

        Streams each sample to the UI via call_from_thread so the table
        populates in real-time during the test.
        """
        result = BandwidthResult(interface=interface, duration=duration)

        baseline = get_io_counters(interface)
        if baseline is None:
            self.app.call_from_thread(
                self._on_error, f"Cannot read counters for interface '{interface}'"
            )
            return

        prev_rx, prev_tx = baseline
        prev_time = time.monotonic()
        start_time = prev_time
        tick = 0

        while True:
            time.sleep(SAMPLE_INTERVAL)
            now = time.monotonic()
            elapsed = now - start_time
            tick += 1

            counters = get_io_counters(interface)
            if counters is None:
                break

            curr_rx, curr_tx = counters
            window = now - prev_time

            rx_mbps = bytes_to_mbps(max(0, curr_rx - prev_rx), window)
            tx_mbps = bytes_to_mbps(max(0, curr_tx - prev_tx), window)

            sample = BandwidthSample(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                rx_mbps=rx_mbps,
                tx_mbps=tx_mbps,
                elapsed=elapsed,
            )
            result.samples.append(sample)

            # Push sample to UI (non-blocking)
            self.app.call_from_thread(
                self._on_sample, sample, tick, duration
            )

            prev_rx, prev_tx = curr_rx, curr_tx
            prev_time = now

            if elapsed >= duration:
                break

        self.app.call_from_thread(self._on_complete, result)

    # ------------------------------------------------------------------
    # UI-thread callbacks
    # ------------------------------------------------------------------

    def _on_sample(self, sample: BandwidthSample, tick: int, duration: int) -> None:
        """Add one live sample row to the DataTable (called on UI thread)."""
        table = self.query_one("#bw-table", DataTable)
        table.add_row(
            sample.timestamp,
            f"{sample.elapsed:.1f}",
            color_mbps(sample.rx_mbps),
            color_mbps(sample.tx_mbps),
        )
        # Scroll to the newest row
        table.scroll_end(animate=False)
        self._update_status(f"⏱ Running — {sample.elapsed:.0f}/{duration}s")

    def _on_complete(self, result: BandwidthResult) -> None:
        """Finalize the test: show summary statistics (called on UI thread)."""
        self._test_running = False
        self._last_result = result
        self._reset_controls()
        self.display_success(f"Test complete — {result.sample_count} samples collected")
        self._update_status(
            f"✅ Done — {result.sample_count} samples over {result.duration}s "
            f"on {result.interface}"
        )
        self._show_summary(result)

    def _on_error(self, message: str) -> None:
        """Handle worker errors on the UI thread."""
        self._test_running = False
        self._reset_controls()
        self.display_error(message)
        self._update_status("❌ Error — see message above")

    def _show_summary(self, result: BandwidthResult) -> None:
        """Render aggregate stats below the table (called on UI thread)."""
        rx_summary = (
            f"[bold]↓ RX[/bold]  "
            f"Avg: [cyan]{format_mbps(result.avg_rx_mbps)}[/cyan]  "
            f"Peak: [green]{format_mbps(result.peak_rx_mbps)}[/green]"
        )
        tx_summary = (
            f"[bold]↑ TX[/bold]  "
            f"Avg: [cyan]{format_mbps(result.avg_tx_mbps)}[/cyan]  "
            f"Peak: [green]{format_mbps(result.peak_tx_mbps)}[/green]"
        )
        self.query_one("#bw-summary-rx", Static).update(rx_summary)
        self.query_one("#bw-summary-tx", Static).update(tx_summary)
