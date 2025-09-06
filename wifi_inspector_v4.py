import platform

# Attempt to import the CoreWLAN framework for macOS
try:
    if platform.system() == "Darwin":
        import CoreWLAN
except ImportError:
    CoreWLAN = None

def inspect_wifi_library_output():
    """
    Directly queries the CoreWLAN library to see exactly what interfaces
    and SSIDs it is reporting, with no other logic.
    """
    if platform.system() != "Darwin":
        print(f"This inspector is designed for macOS. Your OS: {platform.system()}.")
        return

    print("--- Running macOS CoreWLAN Library Inspection ---")
    print("This script will directly query the native Wi-Fi library.")
    print("Please copy and paste the entire output back for analysis.")

    if CoreWLAN is None:
        print("\nERROR: The 'pyobjc-framework-CoreWLAN' library is not installed.")
        print("Please run: pip install pyobjc-framework-CoreWLAN")
        return

    try:
        # Get all available Wi-Fi interface names from the library
        interface_names = CoreWLAN.CWInterface.interfaceNames()

        if not interface_names:
            print("\n>>> CoreWLAN reports: No Wi-Fi hardware interfaces found at all. <<<")
            return

        print(f"\nCoreWLAN found the following interfaces: {list(interface_names)}")

        # Loop through each interface and print its details
        for name in interface_names:
            print(f"\n--- Checking interface: {name} ---")
            interface = CoreWLAN.CWInterface.interfaceWithName_(name)
            
            if not interface:
                print(f"Result: Could not get an interface object for '{name}'.")
                continue

            ssid = interface.ssid()
            bssid = interface.bssid()

            print(f"Result for interface '{name}':")
            print(f"  - SSID: {ssid} (Type: {type(ssid)})")
            print(f"  - BSSID: {bssid} (Type: {type(bssid)})")
            print("---------------------------------")

    except Exception as e:
        print(f"\nAn unexpected error occurred while querying the CoreWLAN library: {e}")

if __name__ == "__main__":
    inspect_wifi_library_output()
