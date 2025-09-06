import platform
import subprocess
import json
import re

# Attempt to import the CoreWLAN framework for macOS
try:
    if platform.system() == "Darwin":
        import CoreWLAN
except ImportError:
    CoreWLAN = None


def inspect_all_wifi_methods():
    """
    Runs a comprehensive suite of macOS Wi-Fi commands and library calls
    to definitively diagnose data retrieval issues.
    """
    if platform.system() != "Darwin":
        print(f"This inspector is designed for macOS. Your OS: {platform.system()}.")
        return

    print("--- Running Final macOS Wi-Fi Inspection ---")
    print("This script will try every known method to get Wi-Fi info.")
    print("Please copy and paste the entire output back for analysis.")

    # --- Method 1: networksetup -listallhardwareports to find the port ---
    wifi_port = None
    print("\n\n--- Method 1: Finding the Wi-Fi Hardware Port ---")
    try:
        command = ["networksetup", "-listallhardwareports"]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        print("[RAW OUTPUT of '-listallhardwareports']")
        print(process.stdout)

        output_lines = process.stdout.splitlines()
        for i, line in enumerate(output_lines):
            if "Hardware Port: Wi-Fi" in line and i + 1 < len(output_lines):
                next_line = output_lines[i + 1]
                port_match = re.search(r"Device:\s*(en\d+)", next_line)
                if port_match:
                    wifi_port = port_match.group(1)
                    print(f"\n[RESULT] Inspector identified Wi-Fi port as: {wifi_port}")
                    break
        if not wifi_port:
            print("\n[RESULT] Inspector could NOT identify the Wi-Fi port.")

    except Exception as e:
        print(f"[ERROR] Could not list hardware ports: {e}")

    # --- Method 2: networksetup -getairportnetwork ---
    print("\n\n--- Method 2: Using 'networksetup' with the discovered port ---")
    if wifi_port:
        try:
            command = ["networksetup", "-getairportnetwork", wifi_port]
            process = subprocess.run(
                command, capture_output=True, text=True, check=True
            )
            print("[RAW OUTPUT of '-getairportnetwork']")
            print(process.stdout)
        except Exception as e:
            print(f"[ERROR] 'networksetup -getairportnetwork' failed: {e}")
    else:
        print("[SKIPPED] because no Wi-Fi port was found in Method 1.")

    # --- Method 3: airport utility (deprecated) ---
    print("\n\n--- Method 3: Using the deprecated 'airport' utility ---")
    try:
        command = [
            "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
            "-I",
        ]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        print("[RAW OUTPUT of 'airport -I']")
        print(process.stdout)
    except Exception as e:
        print(f"[ERROR] 'airport -I' failed: {e}")

    # --- Method 4: wdutil utility ---
    print("\n\n--- Method 4: Using 'wdutil info' (may require sudo) ---")
    try:
        command = ["wdutil", "info"]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        print("[RAW OUTPUT of 'wdutil info']")
        print(process.stdout)
    except Exception as e:
        print(f"[ERROR] 'wdutil info' failed: {e}")

    # --- Method 5: CoreWLAN Library ---
    print("\n\n--- Method 5: Using the native CoreWLAN library ---")
    if CoreWLAN:
        try:
            interface_names = CoreWLAN.CWInterface.interfaceNames()
            print(f"[INFO] CoreWLAN found interfaces: {list(interface_names)}")
            for name in interface_names:
                interface = CoreWLAN.CWInterface.interfaceWithName_(name)
                if interface:
                    print(
                        f"  - Checking '{name}': SSID = {interface.ssid()}, BSSID = {interface.bssid()}"
                    )
                else:
                    print(f"  - Could not get object for interface '{name}'.")
        except Exception as e:
            print(f"[ERROR] CoreWLAN query failed: {e}")
    else:
        print("[ERROR] 'pyobjc-framework-CoreWLAN' library is not installed.")


if __name__ == "__main__":
    inspect_all_wifi_methods()
