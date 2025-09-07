import os
import platform
import socket
import struct
import subprocess
import threading
import time
import requests
import psutil
import re
from netmiko import ConnectHandler
from scapy.all import sniff, inet_ntoa
from scapy.contrib.lldp import LLDPDU
from scapy.contrib.cdp import CDPMsg, CDPAddrRecord


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

        # Get Gateway using the reliable psutil method, with a fallback for macOS
        try:
            gws = psutil.net_if_gateways()
            default_gateway = gws.get("default", {}).get(psutil.AF_INET)
            if default_gateway:
                info["Gateway"] = default_gateway[0]
            else:
                raise Exception("psutil could not find gateway")
        except Exception:
            if platform.system() == "Darwin":
                try:
                    command = "netstat -rn -f inet | grep default | awk '{print $2}'"
                    gateway = subprocess.check_output(
                        command, shell=True, text=True
                    ).strip()
                    if gateway:
                        info["Gateway"] = gateway
                    else:
                        info["Gateway"] = "Could not determine"
                except Exception:
                    info["Gateway"] = "Could not determine"
            else:
                info["Gateway"] = "Could not determine"

        # Get Public IP
        try:
            response = requests.get("https://ipinfo.io/json", timeout=5)
            data = response.json()
            info["Public IP"] = data.get("ip", "N/A")
        except Exception:
            info["Public IP"] = "Error fetching public IP"

        return info

    def get_connection_details(self):
        """Gets details about the active network connection, with special handling for macOS."""
        # macOS specific implementation
        if platform.system() == "Darwin":
            try:
                # Find the default interface using netstat
                command = "netstat -rn -f inet"
                result = subprocess.check_output(command, shell=True, text=True)
                interface = None
                for line in result.splitlines():
                    if line.startswith("default"):
                        parts = line.split()
                        if len(parts) >= 4:
                            gateway, iface = parts[1], parts[3]
                            if all(c in "0123456789." for c in gateway):
                                interface = iface
                                break

                if not interface:
                    return {"Status": "Could not determine default network interface."}

                info = {"Interface": interface}

                # Use system_profiler to get all Wi-Fi details
                try:
                    profiler_cmd = f"system_profiler SPAirPortDataType"
                    profiler_result = subprocess.check_output(
                        profiler_cmd, shell=True, text=True
                    )

                    # Check if the interface is listed as a Wi-Fi card
                    if (
                        f"{interface}:" in profiler_result
                        and "Card Type: Wi-Fi" in profiler_result
                    ):
                        info["Connection Type"] = "Wi-Fi"
                    else:
                        info["Connection Type"] = "Ethernet"

                    if info["Connection Type"] == "Wi-Fi":
                        # Isolate the correct network block
                        network_info_block = re.search(
                            r"Current Network Information:(.*?)(\n\s*\n|$)",
                            profiler_result,
                            re.DOTALL,
                        )
                        if network_info_block:
                            block_text = network_info_block.group(1)

                            # The SSID is the first line in the block, ending with a colon
                            ssid_match = re.search(
                                r"^\s*(.+):$", block_text, re.MULTILINE
                            )
                            if ssid_match:
                                info["SSID"] = ssid_match.group(1).strip()

                            channel = re.search(r"Channel:\s*(.+)", block_text)
                            signal_noise = re.search(
                                r"Signal / Noise:\s*(.+)", block_text
                            )

                            if channel:
                                info["Channel"] = channel.group(1).strip()
                            if signal_noise:
                                parts = signal_noise.group(1).strip().split(" / ")
                                info["Signal"] = parts[0]
                                if len(parts) > 1:
                                    info["Noise"] = parts[1]
                except (subprocess.CalledProcessError, AttributeError):
                    info["Connection Type"] = "Ethernet"  # Fallback if profiler fails

                # Get DNS Servers on macOS
                try:
                    dns_cmd = "scutil --dns | grep 'nameserver\\[[0-9]*\\]' | awk '{print $3}'"
                    dns_result = subprocess.check_output(dns_cmd, shell=True, text=True)
                    dns_servers = list(dict.fromkeys(dns_result.strip().split("\n")))
                    info["DNS Servers"] = ", ".join(dns_servers)
                except Exception:
                    info["DNS Servers"] = "N/A"

                # Get IP and MAC address details from psutil
                addresses = psutil.net_if_addrs().get(interface, [])
                for addr in addresses:
                    if addr.family == socket.AF_INET:
                        info["IP Address"] = addr.address
                        info["Netmask"] = addr.netmask
                    elif addr.family == psutil.AF_LINK:
                        info["MAC Address"] = addr.address

                stats = psutil.net_if_stats().get(interface)
                if stats:
                    info["Status"] = "Up" if stats.isup else "Down"
                    info["Speed"] = f"{stats.speed} Mbps" if stats.speed > 0 else "N/A"
                    info["MTU"] = str(stats.mtu)

                return info

            except Exception as e:
                return {"Error": f"macOS-specific check failed: {e}"}

        # Fallback for other operating systems
        else:
            return {"Status": "Detailed info not yet implemented for this OS."}

    def run_speed_test(self):
        """Performs a network speed test and returns the results."""
        try:
            import speedtest

            st = speedtest.Speedtest()
            st.get_best_server()
            st.download()
            st.upload()

            results = st.results.dict()

            ping = results.get("ping", 0)
            download_speed = results.get("download", 0) / 1_000_000  # Convert to Mbps
            upload_speed = results.get("upload", 0) / 1_000_000  # Convert to Mbps
            server_name = results.get("server", {}).get("name", "N/A")

            return {
                "Ping": f"{ping:.2f} ms",
                "Download": f"{download_speed:.2f} Mbps",
                "Upload": f"{upload_speed:.2f} Mbps",
                "Server": server_name,
            }

        except Exception as e:
            return {"Error": f"Speed test failed: {e}"}

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
                    chassis_id_val = None
                    port_id_val = None
                    port_id_subtype = "N/A"
                    port_description_val = None
                    system_name_val = None
                    mgmt_address_val = None

                    # Manual TLV parsing from raw bytes
                    raw_payload = bytes(packet[LLDPDU].payload)
                    i = 0
                    while i < len(raw_payload):
                        if i + 2 > len(raw_payload):
                            break

                        tlv_header = struct.unpack("!H", raw_payload[i : i + 2])[0]
                        tlv_type = tlv_header >> 9
                        tlv_len = tlv_header & 0x1FF

                        if i + 2 + tlv_len > len(raw_payload):
                            break

                        value_bytes = raw_payload[i + 2 : i + 2 + tlv_len]

                        if tlv_type == 1:  # Chassis ID
                            chassis_id_val = value_bytes[1:]
                        elif tlv_type == 2:  # Port ID
                            port_id_subtype = value_bytes[0]
                            port_id_val = value_bytes[1:]
                        elif tlv_type == 4:  # Port Description
                            port_description_val = value_bytes
                        elif tlv_type == 5:  # System Name
                            system_name_val = value_bytes
                        elif tlv_type == 8:  # Management Address
                            # Mgmt Addr TLV has its own structure
                            if len(value_bytes) > 1:
                                addr_subtype = value_bytes[1]
                                if addr_subtype == 1:  # IPv4
                                    mgmt_address_val = inet_ntoa(value_bytes[2:6])
                        elif tlv_type == 0:  # End of LLDPDU
                            break

                        i += 2 + tlv_len

                    if not chassis_id_val or not port_id_val:
                        raise ValueError(
                            "Essential LLDP fields not found via manual parsing."
                        )

                    # --- Smart Decoding ---
                    chassis_id_str = chassis_id_val.decode("utf-8", "ignore")

                    result = f"--- LLDP Packet Found ---\n"
                    if system_name_val:
                        result += f"System Name: {system_name_val.decode('utf-8', 'ignore')}\n"

                    result += f"Switch ID: {chassis_id_str}\n"

                    if mgmt_address_val:
                        result += f"Management Address: {mgmt_address_val}\n"

                    if port_description_val:
                        result += f"Port Description: {port_description_val.decode('utf-8', 'ignore')}\n"

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
                    mgmt_address = "N/A"
                    if packet.haslayer(CDPAddrRecord):
                        mgmt_address = packet[CDPAddrRecord].addr

                    result = (
                        f"--- CDP Packet Found ---\n"
                        f"Device ID: {device_id}\n"
                        f"Management Address: {mgmt_address}\n"
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
