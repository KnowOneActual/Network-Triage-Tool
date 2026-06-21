"""Verification script to test TrafficHealthMonitor live on Linux."""

from __future__ import annotations

import sys
import time

# Ensure src/ is in python path
from pathlib import Path

src_dir = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(src_dir))

from network_triage.shared.traffic_health import TrafficHealthMonitor


def main() -> None:
    print("====================================================")
    print("TrafficHealthMonitor Live Verification Script")
    print("====================================================")
    print("Initializing monitor...")
    print("Passive sniffing for 5 seconds...")
    print("Note: To capture live traffic, run this script as root (sudo).")
    print("Otherwise, it will fall back to simulation mode.")
    print("----------------------------------------------------")

    monitor = TrafficHealthMonitor()

    def update_callback(m: TrafficHealthMonitor) -> None:
        stats = m.get_stats()
        mode_str = "SIMULATION" if stats["is_simulated"] else "LIVE RAW SOCKETS"
        sys.stdout.write(
            f"\rPkts: {stats['total_packets']} | Rate: {stats['packets_per_second']} pps | Mode: {mode_str}      "
        )
        sys.stdout.flush()

    # Start the monitor
    monitor.start(callback=update_callback)

    # Let it run for 5 seconds
    try:
        time.sleep(5.0)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    # Stop the monitor
    monitor.stop()

    print("\n----------------------------------------------------")
    print("Monitoring completed. Final stats:")
    stats = monitor.get_stats()
    for key, value in stats.items():
        print(f"  {key:<20}: {value}")
    print("====================================================")


if __name__ == "__main__":
    main()
