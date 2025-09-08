import os
import platform
import socket
import struct
import subprocess
import threading
import requests
from netmiko import ConnectHandler
from scapy.all import sniff, inet_ntoa
from scapy.contrib.lldp import LLDPDU
from scapy.contrib.cdp import CDPMsg, CDPAddrRecord


class NetworkTriageToolkitBase:
    """A collection of OS-agnostic network troubleshooting functions."""

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

    def run_speed_test(self):
        """Performs a network speed test and returns the results."""
        try:
            import speedtest

            st = speedtest.Speedtest()
            st.get_best_server()
            st.download()
            st.upload(pre_allocate=False)

            results = st.results.dict()

            ping = results.get("ping", 0)
            download_speed = results.get("download", 0) / 1_000_000
            upload_speed = results.get("upload", 0) / 1_000_000
            server_name = results.get("server", {}).get("name", "N/A")
            isp = results.get("client", {}).get("isp", "N/A")
            jitter = results.get("client", {}).get("jitter", 0)
            packet_loss = results.get("packetLoss", 0)
            result_url = st.results.share()

            return {
                "Ping": f"{ping:.2f} ms",
                "Jitter": f"{jitter:.2f} ms",
                "Download": f"{download_speed:.2f} Mbps",
                "Upload": f"{upload_speed:.2f} Mbps",
                "Packet Loss": f"{packet_loss if packet_loss is not None else 0:.1f}%",
                "Server": server_name,
                "ISP": isp,
                "Result URL": result_url,
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

        packet_found = [False]

        def _packet_callback(packet):
            """This function is called for every captured packet."""
            if self.stop_discovery or packet_found[0]:
                return True

            result = ""
            if packet.haslayer(LLDPDU):
                packet_found[0] = True
                try:
                    chassis_id_val, port_id_val, port_description_val, system_name_val, mgmt_address_val = (None,) * 5
                    raw_payload = bytes(packet[LLDPDU].payload)
                    i = 0
                    while i < len(raw_payload):
                        if i + 2 > len(raw_payload): break
                        tlv_header = struct.unpack("!H", raw_payload[i : i + 2])[0]
                        tlv_type, tlv_len = tlv_header >> 9, tlv_header & 0x1FF
                        if i + 2 + tlv_len > len(raw_payload): break
                        value_bytes = raw_payload[i + 2 : i + 2 + tlv_len]

                        if tlv_type == 1: chassis_id_val = value_bytes[1:]
                        elif tlv_type == 2: port_id_val = value_bytes[1:]
                        elif tlv_type == 4: port_description_val = value_bytes
                        elif tlv_type == 5: system_name_val = value_bytes
                        elif tlv_type == 8 and len(value_bytes) > 1 and value_bytes[1] == 1:
                            mgmt_address_val = inet_ntoa(value_bytes[2:6])
                        elif tlv_type == 0: break
                        i += 2 + tlv_len

                    if not chassis_id_val or not port_id_val:
                        raise ValueError("Essential LLDP fields not found.")

                    result = f"--- LLDP Packet Found ---\n"
                    if system_name_val:
                        result += f"System Name: {system_name_val.decode('utf-8', 'ignore')}\n"
                    result += f"Switch ID: {chassis_id_val.decode('utf-8', 'ignore')}\n"
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
                    device_id, port_id, platform_id = (
                        packet[CDPMsg].device_id.decode(),
                        packet[CDPMsg].port_id.decode(),
                        packet[CDPMsg].platform.decode(),
                    )
                    mgmt_address = next(
                        (addr.addr for addr in packet[CDPMsg].addr if isinstance(addr, CDPAddrRecord)), "N/A"
                    )
                    result = (
                        f"--- CDP Packet Found ---\n"
                        f"Device ID: {device_id}\n"
                        f"Management Address: {mgmt_address}\n"
                        f"Port ID: {port_id}\n"
                        f"Platform: {platform_id}"
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
