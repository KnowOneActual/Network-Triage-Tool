from scapy.all import sniff, wrpcap
from scapy.contrib.lldp import LLDPDU
from scapy.contrib.cdp import CDPMsg
import os
import platform


def inspect_packet():
    """Captures a single LLDP/CDP packet and prints its structure."""
    if platform.system() != "Windows" and os.geteuid() != 0:
        print("This script requires administrator privileges. Please run with 'sudo'.")
        return

    print("Starting packet capture... waiting for one LLDP or CDP packet.")

    packet_found = False

    def packet_callback(packet):
        nonlocal packet_found
        if packet_found:
            return True  # Stop sniffing after one packet is processed

        if packet.haslayer(LLDPDU) or packet.haslayer(CDPMsg):
            packet_found = True
            print("\n" + "=" * 50)
            print("Packet Captured!")
            print("=" * 50)

            # The .show() method prints a detailed breakdown of the packet
            packet.show()

            # Save the packet to a file for analysis in Wireshark
            pcap_file = "captured_packet.pcap"
            wrpcap(pcap_file, packet)
            print("\n" + "=" * 50)
            print(f"Packet details printed above. Packet also saved to '{pcap_file}'")
            print("=" * 50)
            return True  # Tell sniff to stop
        return False

    try:
        sniff(
            filter="ether proto 0x88cc or ether dst 01:00:0c:cc:cc:cc",
            stop_filter=packet_callback,
            timeout=60,  # Stop after 60 seconds if no packet is found
        )
        if not packet_found:
            print("\nNo LLDP or CDP packets were found in 60 seconds.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    inspect_packet()
