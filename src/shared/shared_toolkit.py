import os
import platform
import socket
import struct
import subprocess
import threading
import re
import requests
import psutil
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

    # ... (other functions like get_system_info, run_speed_test, etc., are unchanged) ...

    def run_network_scan(self, target, arguments='-F', callback=None, progress_callback=None):
        """
        Performs an Nmap scan using a direct subprocess for real-time feedback.
        """
        try:
            # Check if Nmap is installed and available
            subprocess.check_output(['nmap', '-V'])
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "Error: Nmap not found. Please ensure it is installed and in your system's PATH."

        try:
            args_list = arguments.split()
            # Add arguments to get progress updates from Nmap
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
                    # Check if the process has been terminated by the stop button
                    if self.nmap_process is None or self.nmap_process.poll() is not None and not line:
                        break

                    output += line
                    if callback:
                        callback(line)

                    # Parse progress from Nmap's verbose output
                    if progress_callback and 'About' in line and '%' in line:
                        match = re.search(r'([\d.]+)% done', line)
                        if match:
                            progress = float(match.group(1))
                            progress_callback(progress)

            # Ensure process is cleaned up
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
    # ... (no change to this class)
    pass
