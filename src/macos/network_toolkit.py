import os
import platform
import socket
import subprocess
import re
import psutil
import requests

# Import the base class and RouterConnection from the shared toolkit
from ..shared.shared_toolkit import NetworkTriageToolkitBase, RouterConnection


class NetworkTriageToolkit(NetworkTriageToolkitBase):
    """macOS-specific network troubleshooting functions."""

    def get_system_info(self):
        """Gathers basic system information, with macOS-specific name resolution."""
        # Start with the basic info as a fallback
        os_string = f"{platform.system()} {platform.release()}"
        hostname = socket.gethostname()

        try:
            # Use the 'sw_vers' command to get the macOS product name and version
            product_name = subprocess.check_output(['sw_vers', '-productName'], text=True).strip()
            product_version = subprocess.check_output(['sw_vers', '-productVersion'], text=True).strip()

            major_version = int(product_version.split('.')[0])

            # Mapping of major macOS versions to marketing names
            marketing_names = {
                15: "Sequoia",
                14: "Sonoma",
                13: "Ventura",
                12: "Monterey",
                11: "Big Sur",
            }

            marketing_name = marketing_names.get(major_version, "")

            # If we found a marketing name, construct the full, user-friendly string
            if marketing_name:
                os_string = f"{product_name} {marketing_name} ({platform.system()} {platform.release()})"
            else:
                os_string = f"{product_name} ({platform.system()} {platform.release()})"

        except Exception as e:
            # If any part of the name resolution fails, we'll just use the basic string
            print(f"Could not resolve macOS marketing name: {e}")

        return {
            "OS": os_string,
            "Hostname": hostname,
        }

    def get_ip_info(self):
        """Fetches local IP, public IP, and gateway information for macOS."""
        info = {
            "Internal IP": "N/A",
            "Gateway": "N/A",
            "Public IP": "N/A",
        }
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                info["Internal IP"] = s.getsockname()[0]
        except Exception:
            info["Internal IP"] = "Error fetching IP"

        try:
            command = "netstat -rn -f inet | grep default | awk '{print $2}'"
            gateway = subprocess.check_output(command, shell=True, text=True).strip()
            info["Gateway"] = gateway if gateway else "Could not determine"
        except Exception:
            info["Gateway"] = "Could not determine"

        try:
            response = requests.get("https://ipinfo.io/json", timeout=5)
            data = response.json()
            info["Public IP"] = data.get("ip", "N/A")
        except Exception:
            info["Public IP"] = "Error fetching public IP"

        return info

    def get_connection_details(self):
        """Gets detailed network connection info on macOS."""
        try:
            command = "netstat -rn -f inet | grep default | awk '{print $4}'"
            interface = subprocess.check_output(command, shell=True, text=True).strip().split('\n')[0]
            if not interface:
                return {"Status": "Could not determine default network interface."}

            info = {"Interface": interface}
            profiler_cmd = "system_profiler SPAirPortDataType"
            profiler_result = subprocess.check_output(profiler_cmd, shell=True, text=True)

            if f"{interface}:" in profiler_result and "Card Type: Wi-Fi" in profiler_result:
                info["Connection Type"] = "Wi-Fi"
                network_info_block = re.search(r"Current Network Information:(.*?)(\n\s*\n|$)", profiler_result, re.DOTALL)
                if network_info_block:
                    block_text = network_info_block.group(1)
                    ssid_match = re.search(r"^\s*(.+):$", block_text, re.MULTILINE)
                    if ssid_match: info["SSID"] = ssid_match.group(1).strip()
                    channel = re.search(r"Channel:\s*(.+)", block_text)
                    if channel: info["Channel"] = channel.group(1).strip()
                    signal_noise = re.search(r"Signal / Noise:\s*(.+)", block_text)
                    if signal_noise:
                        parts = signal_noise.group(1).strip().split(" / ")
                        info["Signal"] = parts[0]
                        if len(parts) > 1: info["Noise"] = parts[1]
            else:
                info["Connection Type"] = "Ethernet"

            dns_cmd = "scutil --dns | grep 'nameserver\\[[0-9]*\\]' | awk '{print $3}'"
            dns_result = subprocess.check_output(dns_cmd, shell=True, text=True)
            dns_servers = list(dict.fromkeys(dns_result.strip().split("\n")))
            info["DNS Servers"] = ", ".join(dns_servers)

            addresses = psutil.net_if_addrs().get(interface, [])
            for addr in addresses:
                if addr.family == socket.AF_INET:
                    info["IP Address"], info["Netmask"] = addr.address, addr.netmask
                elif hasattr(psutil, 'AF_LINK') and addr.family == psutil.AF_LINK:
                    info["MAC Address"] = addr.address

            stats = psutil.net_if_stats().get(interface)
            if stats:
                info["Status"] = "Up" if stats.isup else "Down"
                info["Speed"] = f"{stats.speed} Mbps" if stats.speed > 0 else "N/A"
                info["MTU"] = str(stats.mtu)

            return info

        except Exception as e:
            return {"Error": f"macOS-specific check failed: {e}"}

    def traceroute_test(self, host):
        """Performs a traceroute on macOS."""
        if os.geteuid() != 0:
            return "Traceroute requires administrator privileges. Please run with 'sudo'."
        try:
            command = ["traceroute", "-I", host]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            output, _ = process.communicate(timeout=45)
            return f"--- Traceroute to {host} ---\n{output}"
        except subprocess.TimeoutExpired:
            return f"Traceroute to {host} timed out."
        except FileNotFoundError:
            return "Traceroute command not found."
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    def network_adapter_info(self):
        """Gathers network adapter information on macOS."""
        try:
            return subprocess.check_output(["ifconfig"], text=True, timeout=10)
        except Exception as e:
            return f"Failed to get adapter info: {e}"
