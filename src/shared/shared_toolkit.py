import os
import platform
import socket
import struct
import subprocess
import threading
import re
import requests
import psutil
import speedtest # Make sure to import speedtest
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
        self.nmap_process = None

    def run_speed_test(self):
        """Performs a network speed test and returns the results."""
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            st.download()
            st.upload(pre_allocate=False)

            results = st.results.dict()

            # **THE FIX**: Assume 0.0% packet loss if the key is missing from the results.
            packet_loss = results.get("packetLoss", 0) # Default to 0 if not found
            
            return {
                "Ping": f"{results.get('ping', 0):.2f} ms",
                "Jitter": f"{results.get('client', {}).get('jitter', 0):.2f} ms",
                "Download": f"{results.get('download', 0) / 1_000_000:.2f} Mbps",
                "Upload": f"{results.get('upload', 0) / 1_000_000:.2f} Mbps",
                "Packet Loss": f"{packet_loss:.1f}%",
                "Server": results.get("server", {}).get("name", "N/A"),
                "ISP": results.get("client", {}).get("isp", "N/A"),
                "Result URL": st.results.share() or "N/A",
            }

        except Exception as e:
            return {"Error": f"Speed test failed: {e}"}


    def run_network_scan(self, target, arguments='-F', callback=None, progress_callback=None):
        """
        Performs an Nmap scan using a direct subprocess for real-time feedback.
        """
        try:
            subprocess.check_output(['nmap', '-V'])
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "Error: Nmap not found. Please ensure it is installed and in your system's PATH."

        try:
            args_list = arguments.split()
            if progress_callback:
                if '--stats-every' not in arguments:
                    args_list.extend(['--stats-every', '2s'])
                if '-v' not in arguments:
                    args_list.append('-v')

            command = ['nmap', *args_list, target]

            self.nmap_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            output = ""
            if self.nmap_process and self.nmap_process.stdout:
                for line in iter(self.nmap_process.stdout.readline, ''):
                    if self.nmap_process is None or self.nmap_process.poll() is not None and not line:
                        break

                    output += line
                    if callback:
                        callback(line)

                    if progress_callback and 'About' in line and '%' in line:
                        match = re.search(r'([\d.]+)% done', line)
                        if match:
                            progress = float(match.group(1))
                            progress_callback(progress)

            if self.nmap_process:
                self.nmap_process.wait()
            self.nmap_process = None
            return output

        except Exception as e:
            self.nmap_process = None
            return f"An error occurred during the Nmap scan: {e}"

    def stop_network_scan(self):
        """Stops a running Nmap scan."""
        if self.nmap_process and self.nmap_process.poll() is None:
            try:
                parent = psutil.Process(self.nmap_process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
                self.nmap_process.wait()
                self.nmap_process = None
                return "Scan stopped by user."
            except psutil.NoSuchProcess:
                self.nmap_process = None
                return "Scan already completed."
            except Exception as e:
                return f"Error stopping scan: {e}"
        return "No active scan to stop."


class RouterConnection:
    pass