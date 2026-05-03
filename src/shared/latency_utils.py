"""Latency and Jitter Utilities Module

Provides comprehensive latency measurement including ping statistics,
jitter calculation, and MTR-style tracing with packet loss metrics.

Author: Network-Triage-Tool Contributors
License: MIT
"""

import asyncio
import platform
import re
import statistics
import subprocess
from collections.abc import AsyncGenerator
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from network_triage.logging import get_logger

logger = get_logger(__name__)


class LatencyStatus(Enum):
    """Latency measurement status."""

    SUCCESS = "success"
    TIMEOUT = "timeout"
    UNREACHABLE = "unreachable"
    ERROR = "error"


@dataclass(slots=True)
class PingStatistics:
    """Complete ping statistics result."""

    host: str
    packets_sent: int
    packets_received: int
    packet_loss_percent: float
    min_ms: float
    avg_ms: float
    max_ms: float
    stddev_ms: float  # Jitter indicator
    status: LatencyStatus
    rtt_values: list[float]  # Raw RTT values
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = asdict(self)
        result["status"] = self.status.value
        # Keep rtt_values for reference but limit size
        result["rtt_values"] = self.rtt_values[:100] if self.rtt_values else []
        return {k: v for k, v in result.items() if v is not None}


@dataclass(slots=True)
class TracerouteHop:
    """A single hop in a traceroute path."""

    hop_number: int
    hostname: str | None
    ip_address: str | None
    rtt1_ms: float | None
    rtt2_ms: float | None
    rtt3_ms: float | None
    status: str  # 'responsive', 'timeout', 'error'

    def avg_rtt_ms(self) -> float | None:
        """Calculate average RTT across available samples."""
        times = [t for t in [self.rtt1_ms, self.rtt2_ms, self.rtt3_ms] if t is not None]
        return sum(times) / len(times) if times else None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ping_statistics(
    host: str,
    count: int = 10,
    timeout: int = 5,
    interval: float = 0.5,
    target_stddev: float | None = 1.0,
    min_samples: int = 5,
) -> PingStatistics:
    """Execute ping and calculate comprehensive statistics including jitter.

    Args:
        host: Hostname or IP to ping
        count: Number of ping packets (default 10)
        timeout: Timeout per ping in seconds
        interval: Interval between pings in seconds
        target_stddev: Terminate early if jitter falls below this threshold
        min_samples: Minimum samples before checking early termination

    Returns:
        PingStatistics object with min/max/avg/stddev and jitter

    Example:
        >>> stats = ping_statistics('google.com')
        >>> print(f"Packet loss: {stats.packet_loss_percent}%")
        >>> print(f"Jitter (stddev): {stats.stddev_ms:.2f}ms")

    """
    import time

    result = PingStatistics(
        host=host,
        packets_sent=count,
        packets_received=0,
        packet_loss_percent=0,
        min_ms=0,
        avg_ms=0,
        max_ms=0,
        stddev_ms=0,
        status=LatencyStatus.SUCCESS,
        rtt_values=[],
    )

    # Determine OS-specific ping command
    system = platform.system()

    if system == "Windows":
        # Windows: ping -n <count> <host>
        cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
    else:
        # Linux/macOS: ping -c <count> <host>
        cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
        if system == "Darwin":  # macOS
            cmd = ["ping", "-c", str(count), "-i", str(interval), host]
        else:  # Linux
            cmd = ["ping", "-c", str(count), "-i", str(interval), "-W", str(timeout), host]

    try:
        # Execute ping
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Use text=True instead of universal_newlines=True
        )

        rtt_values: list[float] = []
        stderr_output: str = ""
        start_time = time.time()
        timeout_limit = count * max(timeout, interval) + 5
        early_terminated = False

        if process.stdout is not None:
            while True:
                # Check timeout
                if time.time() - start_time > timeout_limit:
                    process.kill()
                    break

                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                if line:
                    rtts = _parse_ping_output(line, system)
                    rtt_values.extend(rtts)

                    # Statistical sampling early exit
                    if target_stddev is not None and len(rtt_values) >= min_samples:
                        current_stddev = statistics.stdev(rtt_values)
                        if current_stddev <= target_stddev:
                            early_terminated = True
                            process.terminate()
                            break

        if process.stderr is not None:
            stderr_output = process.stderr.read()

        process.wait()

        if not early_terminated and process.returncode not in [0, 1] and not rtt_values:  # 0 = success, 1 = some loss
            result.status = LatencyStatus.UNREACHABLE
            result.error_message = stderr_output or "Ping failed"
            return result

        # If no RTT values but ping succeeded or failed gracefully, calculate packet loss and return
        if not rtt_values:
            result.packets_received = 0
            result.packet_loss_percent = 100.0
            result.status = LatencyStatus.UNREACHABLE
            result.error_message = "No response from host"
            return result

        result.packets_received = len(rtt_values)
        result.rtt_values = rtt_values

        # Calculate statistics
        result.min_ms = min(rtt_values)
        result.max_ms = max(rtt_values)
        result.avg_ms = statistics.mean(rtt_values)
        result.stddev_ms = statistics.stdev(rtt_values) if len(rtt_values) > 1 else 0.0

        actual_count = result.packets_received if early_terminated else count
        result.packet_loss_percent = max(0.0, ((actual_count - result.packets_received) / actual_count) * 100.0)

    except FileNotFoundError:
        result.status = LatencyStatus.ERROR
        result.error_message = "ping command not found"

    except Exception as e:
        result.status = LatencyStatus.ERROR
        result.error_message = str(e)

    return result


def _parse_ping_output(output: str, system: str) -> list[float]:
    """Parse ping output and extract RTT values in milliseconds.

    Args:
        output: Raw ping command output
        system: Operating system ('Windows', 'Linux', 'Darwin')

    Returns:
        List of RTT values in milliseconds

    """
    rtt_values = []

    if system == "Windows":
        # Windows format: "time=15ms"
        pattern = r"time=([\.\d]+)ms"
    else:
        # Linux/macOS format: "time=15.123 ms"
        pattern = r"time=([\.\d]+)\s*ms"

    matches = re.findall(pattern, output)
    rtt_values = [float(m) for m in matches]

    return rtt_values


async def mtr_style_trace_stream(host: str, max_hops: int = 30, timeout_secs: int = 5) -> AsyncGenerator[TracerouteHop]:
    """Perform MTR-style tracing and yield hops as they are discovered.

    Currently uses traceroute fallback since mtr --report doesn't easily stream.
    """
    system = platform.system()

    # Determine traceroute command
    match system:
        case "Windows":
            cmd = ["tracert", "-h", str(max_hops), "-w", str(timeout_secs * 1000), host]
        case "Darwin":
            cmd = ["traceroute", "-m", str(max_hops), "-w", str(timeout_secs), "-n", host]
        case _:  # Linux
            cmd = ["traceroute", "-m", str(max_hops), "-w", str(timeout_secs), "-n", host]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        if process.stdout is not None:
            while True:
                line_bytes = await process.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace")

                if not line.strip() or "traceroute" in line.lower() or "to " in line.lower():
                    continue

                hops = _parse_traceroute_output(line, system)
                for hop in hops:
                    yield hop

        await process.wait()

    except Exception as e:
        logger.error(f"Streaming trace error: {e}")


def mtr_style_trace(host: str, max_hops: int = 30, timeout: int = 5, min_hops: int = 1) -> tuple[list[TracerouteHop], str]:
    """Perform MTR-style tracing combining traceroute with latency statistics.

    Attempts to use 'mtr' command if available, otherwise falls back to
    traceroute + ping for each hop.

    Args:
        host: Destination hostname or IP
        max_hops: Maximum number of hops to trace
        timeout: Timeout for each probe in seconds
        min_hops: Minimum starting hop (usually 1)

    Returns:
        Tuple of (list of TracerouteHop objects, status message)

    Example:
        >>> hops, status = mtr_style_trace('8.8.8.8')
        >>> for hop in hops:
        ...     print(f"Hop {hop.hop_number}: {hop.ip_address} ({hop.avg_rtt_ms():.1f}ms)")

    """
    hops: list[TracerouteHop] = []
    system = platform.system()

    # Try MTR first if available
    if _has_mtr():
        hops, message = _parse_mtr_output(host, max_hops, timeout, system)
        return hops, message

    # Fallback to traceroute + ping
    hops, message = _fallback_trace(host, max_hops, timeout, system)
    return hops, message


def _has_mtr() -> bool:
    """Check if mtr command is available."""
    try:
        subprocess.run(["mtr", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        return True
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False


def _parse_mtr_output(host: str, max_hops: int, timeout: int, system: str) -> tuple[list[TracerouteHop], str]:
    """Parse MTR command output (if mtr is available).

    Args:
        host: Destination
        max_hops: Maximum hops
        timeout: Timeout
        system: OS type

    Returns:
        Tuple of (hops list, status message)

    """
    try:
        # Run mtr in report mode (easy to parse)
        cmd = ["mtr", "--report", "--report-cycles", "3", "--max-hops", str(max_hops), "--timeout", str(timeout), host]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(timeout=max_hops * timeout + 10)

        if process.returncode != 0:
            return [], f"MTR failed: {stderr}"

        hops = _extract_hops_from_mtr(stdout)
        return hops, "MTR trace completed"

    except Exception as e:
        return [], f"MTR error: {e!s}"


def _extract_hops_from_mtr(mtr_output: str) -> list[TracerouteHop]:
    """Extract hop information from MTR report output."""
    hops = []
    lines = mtr_output.split("\n")

    for line in lines:
        # Skip header and summary lines
        if "Hop" in line or "Host" in line or "---" in line or not line.strip():
            continue

        # MTR format: hop_num  host  packets  loss%  snt  last  avg  best  wrst
        parts = line.split()
        if len(parts) < 3:
            continue

        try:
            hop_num = int(parts[0])
            hostname = parts[1]
            # Simplified extraction; full parsing would handle all fields
            hop = TracerouteHop(
                hop_number=hop_num,
                hostname=hostname if hostname != "???" else None,
                ip_address=hostname,  # Simplified
                rtt1_ms=None,
                rtt2_ms=None,
                rtt3_ms=None,
                status="responsive" if hostname != "???" else "timeout",
            )
            hops.append(hop)
        except ValueError:
            continue
        except IndexError:
            continue

    return hops


def _fallback_trace(host: str, max_hops: int, timeout: int, system: str) -> tuple[list[TracerouteHop], str]:
    """Fallback traceroute using subprocess (when mtr unavailable).

    Args:
        host: Destination
        max_hops: Maximum hops
        timeout: Timeout
        system: OS type

    Returns:
        Tuple of (hops list, status message)

    """
    hops = []

    # Determine traceroute command
    match system:
        case "Windows":
            cmd_base = ["tracert", "-h", str(max_hops), "-w", str(timeout * 1000), host]
        case "Darwin":
            cmd_base = ["traceroute", "-m", str(max_hops), "-w", str(timeout), host]
        case _:  # Linux
            cmd_base = ["traceroute", "-m", str(max_hops), "-w", str(timeout), host]

    try:
        process = subprocess.Popen(
            cmd_base,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(timeout=max_hops * timeout + 10)

        if process.returncode == 0:
            hops = _parse_traceroute_output(stdout, system)
            return hops, "Traceroute completed"
        return [], f"Traceroute failed: {stderr}"

    except FileNotFoundError:
        return [], "traceroute command not found"
    except subprocess.TimeoutExpired:
        return hops, f"Traceroute timeout after {max_hops * timeout}s"
    except Exception as e:
        return [], f"Traceroute error: {e!s}"


def _parse_traceroute_output(output: str, system: str) -> list[TracerouteHop]:
    """Parse traceroute output and extract hops with RTT values."""
    hops = []
    lines = output.split("\n")

    for line in lines:
        # Skip empty lines and header
        if not line.strip() or "traceroute" in line.lower() or "to " in line.lower():
            continue

        # Extract hop number
        parts = line.split()
        if not parts or not parts[0].isdigit():
            continue

        try:
            hop_num = int(parts[0])
            remaining = " ".join(parts[1:])

            # Extract hostname/IP and RTT values
            hostname = None
            ip_address = None
            rtt_values = []

            # Pattern: "hostname (ip)  time ms  time ms  time ms"
            if "(" in remaining and ")" in remaining:
                hostname_part = remaining[: remaining.index("(")].strip()
                ip_part = remaining[remaining.index("(") + 1 : remaining.index(")")].strip()
                hostname = hostname_part or None
                ip_address = ip_part
                remaining = remaining[remaining.index(")") + 1 :].strip()

            # Extract RTT values
            time_pattern = r"([\d.]+)\s*ms"
            rtt_matches = re.findall(time_pattern, remaining)
            rtt_values = [float(m) for m in rtt_matches[:3]]

            hop = TracerouteHop(
                hop_number=hop_num,
                hostname=hostname,
                ip_address=ip_address,
                rtt1_ms=rtt_values[0] if len(rtt_values) > 0 else None,
                rtt2_ms=rtt_values[1] if len(rtt_values) > 1 else None,
                rtt3_ms=rtt_values[2] if len(rtt_values) > 2 else None,
                status="responsive" if rtt_values else "timeout",
            )
            hops.append(hop)
        except ValueError:
            continue
        except IndexError:
            continue

    return hops


if __name__ == "__main__":
    # Example usage
    print("\n=== Ping Statistics ===")
    stats = ping_statistics("8.8.8.8", count=5)
    print(f"Host: {stats.host}")
    print(f"Packets: {stats.packets_sent} sent, {stats.packets_received} received")
    print(f"Packet loss: {stats.packet_loss_percent:.1f}%")
    print(f"Min/Avg/Max: {stats.min_ms:.2f}/{stats.avg_ms:.2f}/{stats.max_ms:.2f}ms")
    print(f"Jitter (stddev): {stats.stddev_ms:.2f}ms")

    print("\n=== MTR-Style Trace ===")
    hops, message = mtr_style_trace("8.8.8.8", max_hops=10)
    print(f"Status: {message}")
    print(f"Hops traced: {len(hops)}")
    for hop in hops[:5]:  # Show first 5
        avg_rtt = hop.avg_rtt_ms()
        print(f"Hop {hop.hop_number}: {hop.ip_address} ({avg_rtt:.2f}ms if avg_rtt else 'timeout')")
