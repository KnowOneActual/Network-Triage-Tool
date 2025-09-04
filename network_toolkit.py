import os
import platform
import socket
import subprocess
import threading
import time
import requests
import psutil
from netmiko import ConnectHandler
from scapy.all import sniff
from scapy.contrib.lldp import LLDPDU
from scapy.contrib.cdp import CDPMsg


class NetworkTriageToolkit:
    """A collection of network troubleshooting functions."""

    def __init__(self):
        self.stop_ping_event = threading.Event()
        self.discovery_thread = None
        self.stop_discovery = False

    def get_system_info(self):
        """Gathers basic system information."""
        try:
            return {
                "OS": f"{platform.system()} {platform.release()}",
                "Hostname": socket.gethostname(),
            }
        except Exception as e:
            return {"OS": f"Error: {e}", "Hostname": f"Error: {e}"}

    def get_ip_info(self):
        """Fetches local IP, public IP, and gateway information."""
        info = {
            "Internal IP": "N/A",
            "Gateway": "N/A",
            "Public IP": "N/A",
        }
        # Get Internal IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["Internal IP"] = s.getsockname()[0]
            s.close()
        except Exception:
            info["Internal IP"] = "Error fetching IP"

        # Get Gateway
        try:
            gws = psutil.net_if_addrs()
            # This is a more general way to find the gateway
            for _, addrs in gws.items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        # A bit of a guess, but often works. A more robust solution might be platform-specific.
                        ip_parts = info["Internal IP"].split(".")
                        if ip_parts[0:3] == addr.address.split(".")[0:3]:
                            info["Gateway"] = (
                                ".".join(ip_parts[0:3]) + ".1"
                            )  # Common convention
        except Exception:
            info["Gateway"] = "Could not determine"

        # Get Public IP
        try:
            response = requests.get("https://ipinfo.io/json", timeout=5)
            data = response.json()
            info["Public IP"] = data.get("ip", "N/A")
        except Exception:
            info["Public IP"] = "Error fetching public IP"

        return info

    def continuous_ping(self, host, callback):
        """Pings a host continuously and sends output to a callback."""
        self.stop_ping_event.clear()
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", host]

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
            for line in iter(process.stdout.readline, ""):
                if self.stop_ping_event.is_set():
                    process.terminate()
                    break
                callback(line)
            process.stdout.close()
        except FileNotFoundError:
            callback("Ping command not found. Is it in your system's PATH?")
        except Exception as e:
            callback(f"An error occurred: {e}\n")

    def stop_ping(self):
        """Signals the continuous ping to stop."""
        self.stop_ping_event.set()

    def traceroute_test(self, host):
        """Performs a traceroute to a specific host."""
        if platform.system() != "Windows" and os.geteuid() != 0:
            return "Traceroute on this OS requires administrator privileges. Please run the application with 'sudo'."

        try:
            if platform.system() == "Windows":
                command = ["tracert", "-d", host]
            else:  # Linux/macOS
                command = ["traceroute", "-I", host]  # -I uses ICMP, more reliable

            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            output, _ = process.communicate(timeout=45)

            if (
                process.returncode != 0 and "administrat" in output
            ):  # a more specific check
                return f"Traceroute failed due to permissions. Please run with 'sudo'."
            return f"--- Traceroute to {host} ---\n{output}"

        except subprocess.TimeoutExpired:
            return f"Traceroute to {host} timed out. The host may be unreachable or a firewall is blocking the request."
        except FileNotFoundError:
            return "Traceroute command not found. Ensure it is installed and in your system's PATH."
        except Exception as e:
            return f"An unexpected error occurred during traceroute: {e}"

    def dns_resolution_test(self, domain):
        """Tests DNS resolution for a specific domain."""
        try:
            ip = socket.gethostbyname(domain)
            return f"DNS resolution for {domain}: {ip}"
        except socket.gaierror:
            return f"DNS resolution failed for {domain}. Check your DNS settings."
        except Exception as e:
            return f"An error occurred during DNS resolution: {e}"

    def port_connectivity_test(self, host, port):
        """Tests if a specific port is open on a given host."""
        try:
            port_num = int(port)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex((host, port_num))
                if result == 0:
                    return f"Port {port_num} on {host} is OPEN."
                else:
                    return f"Port {port_num} on {host} is CLOSED or filtered."
        except ValueError:
            return "Invalid port number. Please enter an integer."
        except socket.gaierror:
            return f"Hostname '{host}' could not be resolved."
        except Exception as e:
            return f"An error occurred: {e}"

    def network_adapter_info(self):
        """Gathers detailed network adapter information."""
        try:
            if platform.system() == "Windows":
                command = ["ipconfig", "/all"]
            else:
                command = ["ifconfig"]

            result = subprocess.run(
                command, capture_output=True, text=True, check=True, timeout=10
            )
            return result.stdout
        except FileNotFoundError:
            return "Could not find 'ipconfig' or 'ifconfig'. Please ensure it's in your system PATH."
        except Exception as e:
            return f"Failed to get adapter info: {e}"

    def start_discovery_capture(self, callback, timeout=60):
        """Starts a thread to capture LLDP or CDP packets."""
        if self.discovery_thread and self.discovery_thread.is_alive():
            callback("A scan is already in progress.")
            return

        self.stop_discovery = False
        self.discovery_thread = threading.Thread(
            target=self._run_discovery_capture, args=(callback, timeout), daemon=True
        )
        self.discovery_thread.start()

    def stop_discovery_capture(self):
        """Signals the packet capture thread to stop."""
        self.stop_discovery = True

    def _run_discovery_capture(self, callback, timeout):
        """The actual packet sniffing logic."""
        if platform.system() != "Windows" and os.geteuid() != 0:
            callback(
                "Packet capture requires administrator privileges. Please run with 'sudo'."
            )
            return

        packet_found = [False]  # Use list for mutability in callback

        def _packet_callback(packet):
            """This function is called for every captured packet."""
            if self.stop_discovery or packet_found[0]:
                return True

            result = ""
            if packet.haslayer(LLDPDU):
                packet_found[0] = True
                try:
                    chassis_id = None
                    port_id = None
                    ttl = "N/A"

                    # Manually iterate through TLVs for maximum compatibility
                    if hasattr(packet[LLDPDU], "tlv"):
                        current_tlv = packet[LLDPDU].tlv
                        while isinstance(current_tlv, LLDPDU):
                            if current_tlv.type == 1:  # Chassis ID
                                chassis_id = getattr(current_tlv, "id", None)
                            elif current_tlv.type == 2:  # Port ID
                                port_id = getattr(current_tlv, "id", None)
                            elif current_tlv.type == 3:  # TTL
                                ttl = getattr(current_tlv, "ttl", "N/A")

                            if not hasattr(current_tlv, "payload") or not isinstance(
                                current_tlv.payload, LLDPDU
                            ):
                                break
                            current_tlv = current_tlv.payload

                    if not chassis_id or not port_id:
                        raise ValueError(
                            "Essential LLDP fields (Chassis/Port ID) not found in TLVs."
                        )

                    chassis_id_str = (
                        chassis_id.decode()
                        if isinstance(chassis_id, bytes)
                        else str(chassis_id)
                    )
                    port_id_str = (
                        port_id.decode() if isinstance(port_id, bytes) else str(port_id)
                    )

                    result = (
                        f"--- LLDP Packet Found ---\n"
                        f"Switch ID: {chassis_id_str}\n"
                        f"Port ID: {port_id_str}\n"
                        f"Time-To-Live: {ttl} seconds"
                    )
                except Exception as e:
                    result = f"Error parsing LLDP packet: {e}"

                callback(result)
                return True

            if packet.haslayer(CDPMsg):
                packet_found[0] = True
                try:
                    device_id = packet[CDPMsg].device_id.decode()
                    port_id = packet[CDPMsg].port_id.decode()
                    platform = packet[CDPMsg].platform.decode()
                    result = (
                        f"--- CDP Packet Found ---\n"
                        f"Device ID: {device_id}\n"
                        f"Port ID: {port_id}\n"
                        f"Platform: {platform}"
                    )
                except Exception as e:
                    result = f"Error parsing CDP packet: {e}"

                callback(result)
                return True

            return False

        try:
            sniff(
                filter="ether proto 0x88cc or ether dst 01:00:0c:cc:cc:cc",
                stop_filter=_packet_callback,
                timeout=timeout,
            )
        except Exception as e:
            callback(f"An error occurred during packet capture: {e}")
        finally:
            if not packet_found[0] and not self.stop_discovery:
                callback(
                    f"\nScan complete. No LLDP or CDP packets found in {timeout} seconds."
                )


class RouterConnection:
    """Handles connection and commands for a network device."""

    def __init__(self, device_type, ip, username, password):
        self.device_info = {
            "device_type": device_type,
            "ip": ip,
            "username": username,
            "password": password,
        }
        self.connection = None

    def connect(self):
        """Establishes a connection to the device."""
        try:
            self.connection = ConnectHandler(**self.device_info)
            return "Connection successful."
        except Exception as e:
            self.connection = None
            return f"Connection failed: {e}"

    def disconnect(self):
        """Closes the connection."""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
            return "Disconnected."
        return "No active connection."

    def send_command(self, command):
        """Sends a command to the connected device."""
        if self.connection:
            try:
                output = self.connection.send_command(command)
                return output
            except Exception as e:
                return f"Error sending command: {e}"
        return "Not connected."
