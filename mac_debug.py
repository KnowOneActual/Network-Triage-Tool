import subprocess
import platform


def run_final_debug():
    """
    Runs the two failing macOS-specific commands to gather raw data
    for a definitive diagnosis.
    """
    if platform.system() != "Darwin":
        print("This script is designed for macOS only.")
        return

    print("--- 1. Gateway Information ---")
    try:
        print("DEBUG: Trying to get gateway with psutil...")
        import psutil

        gws = psutil.net_if_gateways()
        default_gateway = gws.get("default", {}).get(psutil.AF_INET)
        if default_gateway:
            print(f"psutil found gateway: {default_gateway[0]}")
        else:
            print("psutil could not find gateway. Trying fallback...")
            command = "netstat -rn -f inet | grep default | awk '{print $2}'"
            gateway = subprocess.check_output(command, shell=True, text=True).strip()
            print(f"Fallback command `netstat...` output: {gateway}")

    except Exception as e:
        print(f"ERROR getting gateway: {e}")

    print("\n" + "=" * 50 + "\n")

    print("--- 2. SSID Information ---")
    try:
        # Find the default interface first
        command = "netstat -rn -f inet | grep default | awk '{print $4}'"
        interface = (
            subprocess.check_output(command, shell=True, text=True)
            .strip()
            .split("\n")[0]
        )

        print(f"DEBUG: Found default interface: {interface}")

        networksetup_cmd = f"networksetup -getairportnetwork {interface}"
        print(f"DEBUG: Running command: '{networksetup_cmd}'")

        networksetup_result = subprocess.check_output(
            networksetup_cmd, shell=True, text=True, stderr=subprocess.STDOUT
        )
        print("RAW OUTPUT of networksetup command:")
        print("---")
        print(networksetup_result)
        print("---")

    except Exception as e:
        print(f"ERROR running networksetup: {e}")


if __name__ == "__main__":
    run_final_debug()
