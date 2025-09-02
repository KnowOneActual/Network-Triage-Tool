import os
import platform
import socket
import subprocess
import threading
import time

import psutil
import requests
from netmiko import ConnectHandler
from scapy.all import sniff
from scapy.contrib.lldp import LLDPDU


class NetworkTriageToolkit:
    """
    A collection of network diagnostic tools.
    Designed to be used by a GUI application. Functions return data
    rather than printing to the console.
    """

    def __init__(self):
        self.ping_process = None
        self.stop_ping_event = threading.Event()
        self.stop_lldp_event = threading.Event()
        self.lldp_found = False

    def get_system_info(self):
        """Gathers basic system information."""
        try:
            info = {
                "OS": f"{platform.system()} {platform.release()}",
                "Hostname": socket.gethostname(),
            }
            return info
        except Exception as e:
            return {"Error": f"Could not get system info: {e}"}

    def get_ip_info(self):
        """Gathers IP address, gateway, and public IP information."""
        info = {
            "Internal IP": "N/A",
            "Gateway": "N/A",
            "Public IP": "N/A",
        }
        try:
            # Get internal IP by connecting to an external server
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                info["Internal IP"] = s.getsockname()[0]
        except Exception as e:
            info["Internal IP"] = f"Error: {e}"

        # Get Gateway
        try:
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    ["ipconfig"],
                    stdout=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                output, _ = process.communicate()
                for line in output.split("\n"):
                    if "Default Gateway" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            gateway = parts[1].strip()
                            if gateway and "::" not in gateway:  # Filter out IPv6
                                info["Gateway"] = gateway
                                break
            else:  # Linux and macOS
                process = subprocess.Popen(
                    ["netstat", "-nr"], stdout=subprocess.PIPE, text=True
                )
                output, _ = process.communicate()
                for line in output.split("\n"):
                    if "default" in line or "0.0.0.0" in line:
                        parts = line.split()
                        if len(parts) > 1:
                            info["Gateway"] = parts[1]
                            break
        except Exception as e:
            info["Gateway"] = f"Error: {e}"

        # Get Public IP
        try:
            response = requests.get("https://api.ipify.org?format=json", timeout=5)
            response.raise_for_status()
            info["Public IP"] = response.json()["ip"]
        except requests.exceptions.RequestException as e:
            info["Public IP"] = f"Error: {e}"

        return info

    def ping_host(self, host, count=4):
        """
        Pings a host a specified number of times.
        Returns the output as a string.
        """
        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, str(count), host]
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if result.stdout:
                return result.stdout
            else:
                return result.stderr
        except Exception as e:
            return f"An error occurred: {e}"

    def continuous_ping(self, host, callback):
        """
        Pings a host continuously and uses a callback to send back updates.
        Stops when the stop_ping_event is set.
        """
        self.stop_ping_event.clear()

        while not self.stop_ping_event.is_set():
            command = (
                ["ping", "-c", "1", host]
                if platform.system().lower() != "windows"
                else ["ping", "-n", "1", host]
            )
            try:
                # Hide the console window on Windows
                startupinfo = None
                if platform.system() == "Windows":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo,
                )
                stdout, stderr = process.communicate(timeout=5)

                if process.returncode == 0:
                    callback(stdout)
                else:
                    callback(
                        stderr
                        if stderr
                        else f"Ping failed with return code: {process.returncode}\n"
                    )

            except subprocess.TimeoutExpired:
                callback(f"Request timed out to {host}\n")
            except Exception as e:
                callback(f"An error occurred: {e}\n")
                break

            if platform.system().lower() != "windows":
                time.sleep(1)

    def stop_ping(self):
        """Sets the event to stop the continuous ping."""
        self.stop_ping_event.set()

    def dns_resolution_test(self, domain):
        """Tests DNS resolution for a specific domain."""
        try:
            ip = socket.gethostbyname(domain)
            return f"Successfully resolved {domain} to: {ip}"
        except socket.gaierror as e:
            return f"DNS resolution failed for {domain}: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    def traceroute_test(self, host):
        """Performs a traceroute to a specific host."""
        if platform.system() in ["Linux", "Darwin"] and os.geteuid() != 0:
            return "Traceroute requires administrator privileges on macOS/Linux.\nPlease run the application with 'sudo'."

        try:
            # Command for Windows
            if platform.system() == "Windows":
                command = ["tracert", "-d", host]
            # Command for macOS/Linux - try ICMP packets first
            else:
                command = ["traceroute", "-I", "-n", host]  # -I for ICMP, -n for no DNS

            result = subprocess.run(command, capture_output=True, text=True, timeout=60)

            # If the command failed, combine stdout and stderr for the error message
            if result.returncode != 0:
                # Fallback for Linux if ICMP trace fails (might be blocked)
                if platform.system() == "Linux" and "-I" in command:
                    command = ["traceroute", "-n", host]  # Default UDP
                    result = subprocess.run(
                        command, capture_output=True, text=True, timeout=60
                    )
                    if result.returncode != 0:
                        return f"Traceroute failed (exit code {result.returncode}):\n{result.stderr}\n{result.stdout}"
                else:
                    return f"Traceroute failed (exit code {result.returncode}):\n{result.stderr}\n{result.stdout}"

            # If successful, return the standard output
            return result.stdout

        except subprocess.TimeoutExpired:
            return f"Traceroute to {host} timed out after 60 seconds."
        except FileNotFoundError:
            return "Traceroute command not found. Is it installed and in your PATH?"
        except Exception as e:
            return f"An unexpected error occurred during traceroute: {e}"

    def port_connectivity_test(self, host, port):
        """Tests if a specific port is open on a given host."""
        try:
            port = int(port)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                if result == 0:
                    return f"Port {port} on {host} is OPEN."
                else:
                    return f"Port {port} on {host} is CLOSED or unreachable."
        except ValueError:
            return "Invalid port. Please enter a number."
        except socket.gaierror:
            return f"Host '{host}' not found or could not be resolved."
        except Exception as e:
            return f"An error occurred during port test: {e}"

    def network_adapter_info(self):
        """Gathers network adapter information using ipconfig/ifconfig."""
        try:
            if platform.system() == "Windows":
                command = ["ipconfig", "/all"]
            else:
                command = ["ifconfig"]

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            return result.stdout
        except FileNotFoundError:
            if platform.system() == "Linux":
                try:
                    command = ["ip", "addr"]
                    result = subprocess.run(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                    )
                    return result.stdout
                except FileNotFoundError:
                    return "Neither 'ifconfig' nor 'ip' command found."
                except Exception as e:
                    return f"Failed to get adapter info with 'ip addr': {e}"
            return "'ifconfig' command not found."
        except Exception as e:
            return f"Failed to retrieve network adapter information: {e}"

    def start_lldp_capture(self, callback, timeout=60):
        """Starts sniffing for LLDP packets on a background thread with a timeout."""
        self.stop_lldp_event.clear()
        self.lldp_found = False

        def process_packet(packet):
            if not self.stop_lldp_event.is_set() and packet.haslayer(LLDPDU):
                self.lldp_found = True
                lldp_info = packet[LLDPDU]
                try:
                    chassis_id_tlv = next(
                        (tlv for tlv in lldp_info.tlvs if tlv.type == 1), None
                    )
                    port_id_tlv = next(
                        (tlv for tlv in lldp_info.tlvs if tlv.type == 2), None
                    )

                    chassis_id = (
                        chassis_id_tlv.id.decode("utf-8", "ignore")
                        if chassis_id_tlv
                        else "N/A"
                    )
                    port_id = (
                        port_id_tlv.id.decode("utf-8", "ignore")
                        if port_id_tlv
                        else "N/A"
                    )

                    result = (
                        f"LLDP Packet Found:\n"
                        f"  Switch Name: {chassis_id}\n"
                        f"  Switch Port: {port_id}\n"
                    )
                    callback(result)
                    self.stop_lldp_event.set()
                except Exception as e:
                    callback(f"Error processing LLDP packet: {e}")
                    self.stop_lldp_event.set()

        def run_sniff():
            """The sniffing function that runs in a thread."""
            try:
                sniff(
                    filter="ether proto 0x88cc",
                    prn=process_packet,
                    stop_filter=lambda p: self.stop_lldp_event.is_set(),
                    timeout=timeout,
                )
            except Exception as e:
                # Only report error if the user didn't manually stop it
                if not self.stop_lldp_event.is_set():
                    callback(f"An error occurred during packet sniffing: {e}")
            finally:
                # This block guarantees that we send a final status update if the scan times out or is stopped.
                if not self.lldp_found and not self.stop_lldp_event.is_set():
                    callback(
                        f"Scan complete. No LLDP packets found in {timeout} seconds."
                    )

        # Check for root/admin privileges before starting the thread
        if platform.system() in ["Linux", "Darwin"] and os.geteuid() != 0:
            callback(
                "LLDP capture requires administrator/root privileges.\nPlease run the application with 'sudo'."
            )
            return

        try:
            thread = threading.Thread(target=run_sniff, daemon=True)
            thread.start()
            callback("LLDP capture started... Listening for packets...")
        except Exception as e:
            callback(f"Error starting LLDP capture: {e}")

    def stop_lldp_capture(self):
        """Stops the LLDP packet capture."""
        self.stop_lldp_event.set()


class RouterConnection:
    """Handles connection and command execution on a network device."""

    def __init__(self, device_type, ip, username, password):
        self.device_info = {
            "device_type": device_type,
            "ip": ip,
            "username": username,
            "password": password,
        }
        self.connection = None

    def connect(self):
        """Establishes the connection to the device."""
        try:
            self.connection = ConnectHandler(**self.device_info)
            return "Connection successful!"
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
        if not self.connection:
            return "Error: Not connected to any device."
        try:
            output = self.connection.send_command(command)
            return output
        except Exception as e:
            return f"Error sending command: {e}"
