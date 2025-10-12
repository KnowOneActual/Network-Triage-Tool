import os
import platform
import socket
import struct
import subprocess
import threading
import re
import requests
import psutil
import speedtest
from netmiko import ConnectHandler
from scapy.all import sniff, inet_ntoa
from scapy.contrib.lldp import LLDPDU
from scapy.contrib.cdp import CDPMsg, CDPAddrRecord
import xml.etree.ElementTree as ET


class NetworkTriageToolkitBase:
    """A collection of OS-agnostic network troubleshooting functions."""

    def __init__(self):
        self.stop_ping_event = threading.Event()
        self.discovery_thread = None
        self.stop_discovery = False
        self.nmap_process = None

    def continuous_ping(self, host, callback):
        """Pings a host continuously and sends output to a callback."""
        self.stop_ping_event.clear()
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

                    if not chassis_id_val or not port_id_val: raise ValueError("Essential LLDP fields not found.")
                    result = f"--- LLDP Packet Found ---\n"
                    if system_name_val: result += f"System Name: {system_name_val.decode('utf-8', 'ignore')}\n"
                    result += f"Switch ID: {chassis_id_val.decode('utf-8', 'ignore')}\n"
                    if mgmt_address_val: result += f"Management Address: {mgmt_address_val}\n"
                    if port_description_val: result += f"Port Description: {port_description_val.decode('utf-8', 'ignore')}\n"
                except Exception as e:
                    result = f"Error parsing LLDP packet: {e}"
                callback(result)
                return True

            if packet.haslayer(CDPMsg):
                packet_found[0] = True
                try:
                    device_id = packet[CDPMsg].device_id.decode()
                    port_id = packet[CDPMsg].port_id.decode()
                    platform_str = packet[CDPMsg].platform.decode()
                    mgmt_address = next((addr.addr for addr in packet[CDPMsg].addr if isinstance(addr, CDPAddrRecord)), "N-A")
                    result = (f"--- CDP Packet Found ---\n"
                              f"Device ID: {device_id}\n"
                              f"Management Address: {mgmt_address}\n"
                              f"Port ID: {port_id}\n"
                              f"Platform: {platform_str}")
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
                callback(f"\nScan complete. No LLDP or CDP packets found in {timeout} seconds.")

    def run_speed_test(self):
        """Performs a network speed test and returns the results."""
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            st.download()
            st.upload(pre_allocate=False)
            results = st.results.dict()
            packet_loss = results.get("packetLoss")
            return {
                "Ping": f"{results.get('ping', 0):.2f} ms",
                "Jitter": f"{results.get('client', {}).get('jitter', 0):.2f} ms",
                "Download": f"{results.get('download', 0) / 1_000_000:.2f} Mbps",
                "Upload": f"{results.get('upload', 0) / 1_000_000:.2f} Mbps",
                "Packet Loss": f"{packet_loss if packet_loss is not None else 0:.1f}%",
                "Server": results.get("server", {}).get("name", "N/A"),
                "ISP": results.get("client", {}).get("isp", "N/A"),
                "Result URL": st.results.share() or "N/A",
            }
        except Exception as e:
            return {"Error": f"Speed test failed: {e}"}

    def run_network_scan(self, target, arguments='-F', callback=None):
        """
        Performs an Nmap scan by running it as a subprocess and parsing the XML output.
        """
        try:
            # Use the full path to Nmap to avoid PATH issues
            command = ["/usr/local/bin/nmap", *arguments.split(), target, "-oX", "-"]
            
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )

            if process.returncode != 0:
                if "command not found" in process.stderr:
                    return [{'ip': 'Error', 'hostname': 'Nmap not found.', 'status': "Please ensure it is installed and in your system's PATH.", 'mac': '', 'vendor': '', 'details': {}}]
                return [{'ip': 'Error', 'hostname': 'An Nmap error occurred.', 'status': process.stderr.strip(), 'mac': '', 'vendor': '', 'details': {}}]

            root = ET.fromstring(process.stdout)
            results = []
            
            for host in root.findall('host'):
                status_elem = host.find('status')
                status = status_elem.get('state') if status_elem is not None else 'unknown'
                
                if status != 'up':
                    continue

                addr_elem = host.find("address[@addrtype='ipv4']")
                ip_addr = addr_elem.get('addr') if addr_elem is not None else 'N/A'
                
                mac_elem = host.find("address[@addrtype='mac']")
                mac_addr = mac_elem.get('addr') if mac_elem is not None else ''
                vendor = mac_elem.get('vendor') if mac_elem is not None else ''
                
                hostname_elem = host.find("hostnames/hostname")
                hostname = hostname_elem.get('name') if hostname_elem is not None else ''
                
                host_details = {
                    'ip': ip_addr, 'hostname': hostname, 'status': status,
                    'mac': mac_addr, 'vendor': vendor, 'details': {}
                }

                os_match_elem = host.find("os/osmatch")
                if os_match_elem is not None:
                    host_details['details']['os'] = os_match_elem.get('name', 'N/A')

                host_details['details']['ports'] = []
                ports_elem = host.find('ports')
                if ports_elem is not None:
                    for port in ports_elem.findall('port'):
                        service_elem = port.find('service')
                        port_info = {
                            'port': port.get('portid'),
                            'protocol': port.get('protocol'),
                            'state': port.find('state').get('state'),
                            'name': service_elem.get('name', '') if service_elem is not None else '',
                            'product': service_elem.get('product', '') if service_elem is not None else '',
                            'version': service_elem.get('version', '') if service_elem is not None else ''
                        }
                        host_details['details']['ports'].append(port_info)

                results.append(host_details)
            
            return results

        except FileNotFoundError:
             return [{'ip': 'Error', 'hostname': 'Nmap not found.', 'status': "Please ensure it is installed and in your system's PATH.", 'mac': '', 'vendor': '', 'details': {}}]
        except ET.ParseError:
            return [{'ip': 'Error', 'hostname': 'Failed to parse Nmap output.', 'status': 'The scan may have been interrupted or produced invalid XML.', 'mac': '', 'vendor': '', 'details': {}}]
        except Exception as e:
            return [{'ip': 'Error', 'hostname': 'An unexpected error occurred.', 'status': str(e), 'mac': '', 'vendor': '', 'details': {}}]

    def stop_network_scan(self):
        """Stops a running Nmap scan."""
        return "Scan stopping is not directly supported with this method."


class RouterConnection:
    pass