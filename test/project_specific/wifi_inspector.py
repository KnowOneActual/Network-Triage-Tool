import platform
import subprocess
import os


def inspect_wifi_output():
    """
    Runs the native OS command for Wi-Fi details and prints the raw output.
    """
    system = platform.system()
    print(f"--- Running Wi-Fi inspection for {system} ---")

    if system == "Darwin":  # macOS
        airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        if not os.path.exists(airport_path):
            print("Error: Airport utility not found at the expected path.")
            return

        command = [airport_path, "-I"]
        try:
            process = subprocess.run(
                command, capture_output=True, text=True, check=True
            )
            print("\n--- Raw Airport Output ---")
            print(process.stdout)
            print("--------------------------")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"\nError running airport command: {e}")
            print("Is your Wi-Fi turned on and connected?")

    else:
        print(f"This inspector is designed for macOS. Your OS: {system}.")
        print("No action taken.")


if __name__ == "__main__":
    inspect_wifi_output()
