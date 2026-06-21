"""Traffic Health monitoring and history comparison for Phase 5."""

from __future__ import annotations

import json
import random
import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

from scapy.all import sniff
from scapy.packet import Packet

# Default directory to store traffic capture history
HISTORY_DIR = Path.home() / ".config" / "network-triage"
HISTORY_FILE = HISTORY_DIR / "traffic_history.json"


class TrafficHealthMonitor:
    """Monitors local traffic type distribution and broadcast protocols passively."""

    def __init__(self) -> None:
        self._sniff_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.is_running = False
        self.is_simulated = False
        self._rng = random.SystemRandom()
        self.reset()

    def reset(self) -> None:
        """Reset counters and timer."""
        self.total_packets = 0
        self.unicast_packets = 0
        self.broadcast_packets = 0
        self.multicast_packets = 0

        # Protocol counters
        self.arp_packets = 0
        self.dhcp_packets = 0
        self.stp_packets = 0
        self.lldp_packets = 0
        self.cdp_packets = 0

        # IP and transport protocols
        self.ipv4_packets = 0
        self.ipv6_packets = 0
        self.tcp_packets = 0
        self.udp_packets = 0
        self.icmp_packets = 0
        self.dns_packets = 0

        self.start_time = time.time()
        self.is_simulated = False

    def start(
        self,
        callback: Callable[[TrafficHealthMonitor], None] | None = None,
        interface: str | None = None,
    ) -> None:
        """Start the passive packet sniffing in a background thread."""
        if self.is_running:
            return
        self.reset()
        self.is_running = True
        self._stop_event.clear()
        self._sniff_thread = threading.Thread(
            target=self._run_sniffing,
            args=(callback, interface),
            daemon=True,
        )
        self._sniff_thread.start()

    def stop(self) -> None:
        """Stop packet sniffing."""
        self._stop_event.set()
        self.is_running = False

    def get_stats(self) -> dict[str, Any]:
        """Get the current accumulated packet statistics."""
        elapsed = time.time() - self.start_time
        pps = self.total_packets / elapsed if elapsed > 0 else 0.0
        return {
            "total_packets": self.total_packets,
            "unicast_packets": self.unicast_packets,
            "broadcast_packets": self.broadcast_packets,
            "multicast_packets": self.multicast_packets,
            "arp_packets": self.arp_packets,
            "dhcp_packets": self.dhcp_packets,
            "stp_packets": self.stp_packets,
            "lldp_packets": self.lldp_packets,
            "cdp_packets": self.cdp_packets,
            "ipv4_packets": self.ipv4_packets,
            "ipv6_packets": self.ipv6_packets,
            "tcp_packets": self.tcp_packets,
            "udp_packets": self.udp_packets,
            "icmp_packets": self.icmp_packets,
            "dns_packets": self.dns_packets,
            "elapsed_seconds": elapsed,
            "packets_per_second": round(pps, 2),
            "is_simulated": self.is_simulated,
        }

    def _run_sniffing(self, callback: Callable[[TrafficHealthMonitor], None] | None, interface: str | None) -> None:
        """Runs the sniffing loop, falling back to simulation if permissions are lacking."""

        def _packet_callback(packet: Packet) -> None:
            if self._stop_event.is_set():
                return

            self.total_packets += 1

            # Destination MAC check
            dst_mac = getattr(packet, "dst", None)
            if dst_mac:
                if dst_mac == "ff:ff:ff:ff:ff:ff":
                    self.broadcast_packets += 1
                else:
                    try:
                        # Multicast MACs have the least significant bit of the first octet set (odd value)
                        first_octet = int(dst_mac.split(":")[0], 16)
                        if first_octet & 1:
                            self.multicast_packets += 1
                        else:
                            self.unicast_packets += 1
                    except Exception:
                        self.unicast_packets += 1
            else:
                self.unicast_packets += 1

            # Protocol detection
            if packet.haslayer("ARP"):
                self.arp_packets += 1
            if packet.haslayer("DHCP") or packet.haslayer("BOOTP"):
                self.dhcp_packets += 1
            if packet.haslayer("LLDPDU") or packet.haslayer("LLDP"):
                self.lldp_packets += 1
            if packet.haslayer("CDPMsg") or packet.haslayer("CDP"):
                self.cdp_packets += 1
            if dst_mac == "01:80:c2:00:00:00" or packet.haslayer("STP"):
                self.stp_packets += 1

            # L3 checks
            if packet.haslayer("IP"):
                self.ipv4_packets += 1
            elif packet.haslayer("IPv6"):
                self.ipv6_packets += 1

            # L4/App checks
            if packet.haslayer("TCP"):
                self.tcp_packets += 1
            elif packet.haslayer("UDP"):
                self.udp_packets += 1
                if packet.haslayer("DNS") or (getattr(packet, "sport", 0) == 53 or getattr(packet, "dport", 0) == 53):
                    self.dns_packets += 1
            elif packet.haslayer("ICMP") or packet.haslayer("ICMPv6"):
                self.icmp_packets += 1

            if callback:
                try:
                    callback(self)
                except Exception:
                    pass

        try:
            sniff_kwargs: dict[str, Any] = {
                "prn": _packet_callback,
                "store": 0,
                "timeout": 1.0,  # Sniff in 1s blocks so we can check the stop event
            }
            if interface:
                sniff_kwargs["iface"] = interface

            # Test permission by attempting to open a sniff session once
            sniff(**{**sniff_kwargs, "count": 1, "timeout": 0.1})

            # Sniff loop
            while not self._stop_event.is_set():
                sniff(**sniff_kwargs)

        except OSError:
            # Fall back to simulation mode
            self.is_simulated = True
            while not self._stop_event.is_set():
                time.sleep(self._rng.uniform(0.1, 0.4))
                self.total_packets += 1

                # Pick packet type distribution
                r = self._rng.random()
                if r < 0.65:
                    self.unicast_packets += 1
                    # Protocols for unicast
                    r2 = self._rng.random()
                    if r2 < 0.6:
                        self.tcp_packets += 1
                        self.ipv4_packets += 1
                    elif r2 < 0.9:
                        self.udp_packets += 1
                        self.ipv4_packets += 1
                        if self._rng.random() < 0.15:
                            self.dns_packets += 1
                    else:
                        self.ipv6_packets += 1
                        self.tcp_packets += 1
                elif r < 0.88:
                    self.multicast_packets += 1
                    r2 = self._rng.random()
                    if r2 < 0.35:
                        self.stp_packets += 1
                    elif r2 < 0.6:
                        self.lldp_packets += 1
                    elif r2 < 0.8:
                        self.cdp_packets += 1
                    else:
                        self.ipv6_packets += 1
                else:
                    self.broadcast_packets += 1
                    r2 = self._rng.random()
                    if r2 < 0.7:
                        self.arp_packets += 1
                    else:
                        self.dhcp_packets += 1
                        self.udp_packets += 1
                        self.ipv4_packets += 1

                if callback:
                    try:
                        callback(self)
                    except Exception:
                        pass

    def save_to_history(self) -> None:
        """Saves current statistics to a JSON history file."""
        stats = self.get_stats()
        stats["timestamp"] = datetime.now().isoformat()

        # Load existing history
        history = self.load_history()
        history.append(stats)

        # Retain only last 50 entries
        history = history[-50:]

        try:
            HISTORY_DIR.mkdir(parents=True, exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
        except Exception:
            pass

    @staticmethod
    def load_history() -> list[dict[str, Any]]:
        """Loads and returns all history entries from the JSON file."""
        if not HISTORY_FILE.exists():
            return []
        try:
            with open(HISTORY_FILE, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return cast("list[dict[str, Any]]", data)
                return []
        except Exception:
            return []

    def get_yesterday_comparison(self) -> dict[str, Any] | None:
        """Finds a history record from 'yesterday' to compare with current stats."""
        history = self.load_history()
        if not history:
            return None

        # Look for a record between 12 and 36 hours ago
        now = datetime.now()
        yesterday_min = now - timedelta(hours=36)
        yesterday_max = now - timedelta(hours=12)

        for entry in reversed(history):
            try:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if yesterday_min <= entry_time <= yesterday_max:
                    return entry
            except (KeyError, ValueError):
                continue

        # Fallback: return the most recent record that is at least 1 hour old
        fallback_limit = now - timedelta(hours=1)
        for entry in reversed(history):
            try:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time <= fallback_limit:
                    return entry
            except (KeyError, ValueError):
                continue

        return None
