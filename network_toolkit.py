#
# This library combines the logic from your various scripts into a single
# backend module that the GUI application can call.

import os
import platform
import socket
import subprocess
import threading
from datetime import datetime

# Dependencies to install:
# pip install netmiko scapy psutil requests
from netmiko import ConnectHandler
from scapy.all import sniff
from scapy.contrib.lldp import LLDPDU
import psutil
import requests


# --- Section 1: Client-Side Information (Inspired by nettest.sh and NTS_V3) ---


def get_host_info():
    """Gathers basic host information."""
    return {
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
    }


def get_ip_info():
    """Gets local IP, default gateway, and public IP."""
    info = {"internal_ip": "N/A", "gateway": "N/A", "external_ip": "N/A"}
    try:
        # Using psutil for cross-platform network info
        addrs = psutil.net_if_addrs()
        gateways = psutil.net_if_gateways()

        default_gateway_info = gateways.get("default", {})
        if psutil.AF_INET in default_gateway_info:
            gateway_ip, iface = default_gateway_info[psutil.AF_INET]
            info["gateway"] = gateway_ip

            if iface in addrs:
                for addr in addrs[iface]:
                    if addr.family == socket.AF_INET:
                        info["internal_ip"] = addr.address
                        break
    except Exception as e:
        print(f"Error getting local IP/Gateway: {e}")

    try:
        # Use requests for a more reliable public IP lookup
        response = requests.get("https://ipinfo.io/json", timeout=5)
        response.raise_for_status()
        data = response.json()
        info["external_ip"] = data.get("ip", "N/A")
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch external IP: {e}")

    return info


def get_network_adapter_info():
    """Gathers detailed network adapter information (ipconfig/ifconfig)."""
    try:
        if platform.system() == "Windows":
            command = ["ipconfig", "/all"]
        elif platform.system() == "Linux":
            command = ["ip", "a"]
        else:  # MacOS/Other Unix-like
            command = ["ifconfig"]

        response = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return response.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return f"Failed to retrieve network adapter info: {e}"


# --- Section 2: Active Probing Tools (Inspired by ping_logger.py, LLDP_hunt.py, NTS_V3) ---


def run_ping(host, count=4):
    """Pings a host a specific number of times and returns the full output."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, str(count), host]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
        return result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return f"Ping failed: {e}"


def run_dns_lookup(domain):
    """Performs a DNS lookup and returns the IP address."""
    try:
        ip = socket.gethostbyname(domain)
        return f"DNS resolution for {domain}: {ip}"
    except socket.gaierror as e:
        return f"DNS resolution failed for {domain}: {e}"


def run_traceroute(host, callback):
    """Performs a traceroute and uses a callback to return each line of output."""
    command = (
        ["tracert", "-d", host]
        if platform.system() == "Windows"
        else ["traceroute", "-n", host]
    )
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in iter(process.stdout.readline, ""):
            callback(line.strip())
        process.stdout.close()
        process.wait()
    except FileNotFoundError:
        callback(f"Error: '{command[0]}' not found.")
    except Exception as e:
        callback(f"An error occurred: {e}")


def run_port_scan(host, port):
    """Tests if a specific port is open on a given host."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            return f"Port {port} on {host} is OPEN."
        else:
            return f"Port {port} on {host} is CLOSED or unreachable."
    except socket.gaierror:
        return f"Host '{host}' not found or could not be resolved."
    except Exception as e:
        return f"An error occurred during port test: {e}"
    finally:
        sock.close()


def run_lldp_scan(callback, duration=15):
    """
    Captures LLDP packets for a short duration and uses a callback to return the result.
    Should be run in a thread to not block the GUI.
    """
    discovered_data = {}

    def process_packet(packet):
        if packet.haslayer(LLDPDU):
            try:
                chassis_id_tlv = packet[LLDPDU].tlvlist[0]
                port_id_tlv = packet[LLDPDU].tlvlist[1]

                discovered_data["switch_name"] = chassis_id_tlv.id.decode()
                discovered_data["port_id"] = port_id_tlv.id.decode()

                for tlv in packet[LLDPDU].tlvlist:
                    if tlv.type == 5:  # System Description
                        discovered_data["switch_model"] = tlv.description.decode()
                        break
                return True  # Stop sniffing
            except (IndexError, AttributeError, UnicodeDecodeError) as e:
                print(f"Error parsing LLDP packet: {e}")
        return False

    try:
        sniff(
            prn=process_packet,
            filter="ether dst 01:80:c2:00:00:0e",
            stop_filter=process_packet,
            timeout=duration,
        )
        if discovered_data:
            callback(discovered_data)
        else:
            callback({"error": "No LLDP packets detected."})
    except Exception as e:
        callback(
            {
                "error": f"Failed to start packet capture. Run with admin/sudo rights. Details: {e}"
            }
        )


# --- Section 3: Device Diagnostics (From RouterHelper.py) ---


class RouterConnection:
    """A wrapper for Netmiko to connect and run commands on network devices."""

    def __init__(self, device_type, ip, username, password):
        self.device_info = {
            "device_type": device_type,
            "ip": ip,
            "username": username,
            "password": password,
        }
        self.connection = None

    def connect(self):
        """Establishes the connection."""
        if self.connection:
            return "Already connected."
        try:
            self.connection = ConnectHandler(**self.device_info)
            return f"Successfully connected to {self.device_info['ip']}."
        except Exception as e:
            self.connection = None
            return f"Error: {e}"

    def disconnect(self):
        """Closes the connection."""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
            return "Disconnected."
        return "Not connected."

    def send_command(self, command):
        """Sends a command and returns the output."""
        if not self.connection:
            return "Error: Not connected to any device."
        try:
            output = self.connection.send_command(command)
            return output
        except Exception as e:
            return f"Error executing command: {e}"
