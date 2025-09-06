import platform
import subprocess
import json


def inspect_wifi_output_v2():
    """
    Runs multiple native macOS commands for Wi-Fi details and prints their raw output.
    """
    if platform.system() != "Darwin":
        print(f"This inspector is designed for macOS. Your OS: {platform.system()}.")
        return

    print("--- Running macOS Wi-Fi Inspection ---")
    print("This script will run several commands to help debug Wi-Fi data collection.")
    print("Please copy and paste the entire output back for analysis.")

    # --- Test 1: networksetup ---
    print("\n\n--- Test 1: networksetup -getairportnetwork en0 ---")
    try:
        command = ["networksetup", "-getairportnetwork", "en0"]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        print("--- Raw Output ---")
        print(process.stdout)
        print("------------------")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error running command: {e}")
        if hasattr(e, "stderr") and e.stderr:
            print(f"--- Stderr ---")
            print(e.stderr)
            print("--------------")

    # --- Test 2: wdutil ---
    print("\n\n--- Test 2: wdutil info ---")
    try:
        command = ["wdutil", "info"]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        print("--- Raw Output ---")
        print(process.stdout)
        print("------------------")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error running command: {e}")
        if hasattr(e, "stderr") and e.stderr:
            print(f"--- Stderr ---")
            print(e.stderr)
            print("--------------")

    # --- Test 3: system_profiler ---
    print(
        "\n\n--- Test 3: system_profiler SPNetworkDataType -json (Wi-Fi section only) ---"
    )
    try:
        command = ["system_profiler", "SPNetworkDataType", "-json"]
        process = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=15
        )
        network_data = json.loads(process.stdout)
        wifi_info_found = False
        for service in network_data.get("SPNetworkDataType", []):
            if "spnetwork_airport_information" in service:
                wifi_info_found = True
                print("--- Raw JSON Output (Wi-Fi Part) ---")
                print(json.dumps(service, indent=2))
                print("------------------------------------")
                break
        if not wifi_info_found:
            print("No Wi-Fi information found in system_profiler output.")

    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as e:
        print(f"Error running command: {e}")
        if hasattr(e, "stderr") and e.stderr:
            print(f"--- Stderr ---")
            print(e.stderr)
            print("--------------")


if __name__ == "__main__":
    inspect_wifi_output_v2()
