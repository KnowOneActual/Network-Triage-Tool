"""macOS-specific network troubleshooting functions.

Provides network diagnostics optimized for macOS systems using native tools
like system_profiler, networksetup, and scutil for reliable data gathering.
"""

import os
import platform
import socket
import subprocess
import re
import psutil
import requests
import logging

from ..shared.shared_toolkit import NetworkTriageToolkitBase
from ..exceptions import (
    NetworkCommandError,
    PrivilegeError,
    CommandNotFoundError,
    ParseError,
    NetworkConnectivityError,
)
from ..utils import (
    safe_subprocess_run,
    safe_socket_operation,
    safe_http_request,
    retry,
    format_error_message,
    log_exception,
)

logger = logging.getLogger(__name__)


class NetworkTriageToolkit(NetworkTriageToolkitBase):
    """macOS-specific network troubleshooting functions.
    
    This toolkit uses macOS-native commands like system_profiler, networksetup,
    and scutil for reliable network diagnostics. It includes comprehensive error
    handling for common failure modes.
    """

    def get_system_info(self) -> dict:
        """Gather basic system information with macOS-specific name resolution.
        
        Returns:
            dict: Contains 'OS' (with marketing name) and 'Hostname'
        
        Examples:
            {'OS': 'macOS Sonoma (Darwin 23.1.0)', 'Hostname': 'MacBook.local'}
        """
        try:
            os_string = f"{platform.system()} {platform.release()}"
            hostname = socket.gethostname()
            
            try:
                # Get marketing name from system
                product_name = safe_subprocess_run(
                    ['sw_vers', '-productName'],
                    timeout=5,
                    check_command_exists=False,
                )
                product_version = safe_subprocess_run(
                    ['sw_vers', '-productVersion'],
                    timeout=5,
                    check_command_exists=False,
                )
                
                # Parse major version and map to marketing name
                major_version = int(product_version.split('.')[0])
                marketing_names = {
                    15: "Sequoia", 14: "Sonoma", 13: "Ventura",
                    12: "Monterey", 11: "Big Sur", 10: "Catalina",
                }
                marketing_name = marketing_names.get(major_version, "")
                
                if marketing_name:
                    os_string = f"{product_name} {marketing_name} ({platform.system()} {platform.release()})"
                else:
                    os_string = f"{product_name} ({platform.system()} {platform.release()})"
            
            except (CommandNotFoundError, ParseError) as e:
                logger.debug(f"Could not resolve macOS marketing name: {e}. Using fallback.")
                # Fallback to generic Darwin version
                os_string = f"macOS ({platform.system()} {platform.release()})"
            
            return {"OS": os_string, "Hostname": hostname}
        
        except Exception as e:
            log_exception(e, context="get_system_info")
            return {"OS": "N/A", "Hostname": "N/A"}

    def get_ip_info(self) -> dict:
        """Fetch local IP, public IP, and gateway information.
        
        Returns:
            dict: Contains 'Internal IP', 'Gateway', and 'Public IP'
        
        Examples:
            {
                'Internal IP': '192.168.1.42',
                'Gateway': '192.168.1.1',
                'Public IP': '203.0.113.42'
            }
        """
        info = {"Internal IP": "N/A", "Gateway": "N/A", "Public IP": "N/A"}
        
        # Get internal IP via socket connection
        try:
            def _get_internal_ip():
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    # Connect to a non-routable address (doesn't actually connect)
                    s.connect(("8.8.8.8", 80))
                    return s.getsockname()[0]
            
            info["Internal IP"] = safe_socket_operation(
                _get_internal_ip,
                timeout=3,
                operation_name="Get internal IP",
            )
        except Exception as e:
            logger.debug(f"Could not get internal IP: {e}")
            info["Internal IP"] = "Error fetching IP"
        
        # Get gateway via netstat
        try:
            gateway = safe_subprocess_run(
                ["netstat", "-rn", "-f", "inet"],
                timeout=5,
                check_command_exists=False,
            )
            # Parse netstat output for default gateway
            for line in gateway.split('\n'):
                if 'default' in line:
                    parts = line.split()
                    if len(parts) > 1:
                        info["Gateway"] = parts[1]
                        break
            
            if info["Gateway"] == "N/A":
                info["Gateway"] = "Could not determine"
        
        except (CommandNotFoundError, NetworkCommandError) as e:
            logger.debug(f"Could not get gateway: {e}")
            info["Gateway"] = "Could not determine"
        
        # Get public IP via HTTP request
        try:
            data = safe_http_request('https://ipinfo.io/json', timeout=5, retries=2)
            info["Public IP"] = data.get("ip", "N/A")
        except NetworkConnectivityError as e:
            logger.debug(f"Could not get public IP: {e}")
            info["Public IP"] = "Error fetching public IP"
        
        return info

    def get_connection_details(self) -> dict:
        """Get detailed network connection info using system_profiler and psutil.
        
        Returns:
            dict: Comprehensive connection details including Wi-Fi info
        
        Examples:
            {
                'Interface': 'en0',
                'Connection Type': 'Wi-Fi',
                'IP Address': '192.168.1.42',
                'SSID': 'HomeNetwork',
                'Signal': '-40 dBm',
                'Channel': '11',
                ...
            }
        """
        try:
            # Get primary network interface
            try:
                interface_name = safe_subprocess_run(
                    ["netstat", "-rn", "-f", "inet"],
                    timeout=5,
                    check_command_exists=False,
                )
                # Parse netstat output
                for line in interface_name.split('\n'):
                    if 'default' in line:
                        parts = line.split()
                        if len(parts) > 3:
                            interface_name = parts[3]
                            break
                
                if not interface_name:
                    return {"Error": "Could not determine primary network interface."}
            
            except NetworkCommandError as e:
                logger.debug(f"netstat failed: {e}. Trying alternative method.")
                return {"Error": f"Could not determine network interface: {e}"}
            
            info = {"Interface": interface_name}
            
            # Get Wi-Fi details using system_profiler
            try:
                profiler_output = safe_subprocess_run(
                    ["system_profiler", "SPAirPortDataType"],
                    timeout=10,
                    check_command_exists=False,
                )
                
                if f"{interface_name}:" in profiler_output and "Card Type: Wi-Fi" in profiler_output:
                    info["Connection Type"] = "Wi-Fi"
                    
                    # Parse Current Network Information section
                    network_info_block = re.search(
                        r"Current Network Information:(.*?)(?:Other Local Wi-Fi Networks:|\Z)",
                        profiler_output,
                        re.DOTALL
                    )
                    
                    if network_info_block:
                        block_text = network_info_block.group(1)
                        
                        # Extract SSID
                        ssid_match = re.search(r"^\s*(.+):$", block_text, re.MULTILINE)
                        if ssid_match:
                            info["SSID"] = ssid_match.group(1).strip()
                        
                        # Extract Channel
                        channel_match = re.search(r"Channel:\s*(.+)", block_text)
                        if channel_match:
                            info["Channel"] = channel_match.group(1).strip()
                        
                        # Extract Signal/Noise
                        signal_noise_match = re.search(r"Signal / Noise:\s*(.+)", block_text)
                        if signal_noise_match:
                            parts = signal_noise_match.group(1).strip().split(" / ")
                            info["Signal"] = parts[0]
                            if len(parts) > 1:
                                info["Noise"] = parts[1]
                else:
                    info["Connection Type"] = "Ethernet"
            
            except (CommandNotFoundError, NetworkCommandError) as e:
                logger.debug(f"system_profiler failed: {e}. Assuming Ethernet.")
                info["Connection Type"] = "Ethernet"
            
            # Get DNS servers using scutil
            try:
                dns_output = safe_subprocess_run(
                    ["scutil", "--dns"],
                    timeout=5,
                    check_command_exists=False,
                )
                # Parse DNS servers
                dns_servers = set()
                for line in dns_output.split('\n'):
                    if 'nameserver[' in line:
                        parts = line.split()
                        if len(parts) > 0:
                            dns_servers.add(parts[-1])
                
                info["DNS Servers"] = ", ".join(sorted(dns_servers)) if dns_servers else "N/A"
            
            except (CommandNotFoundError, NetworkCommandError) as e:
                logger.debug(f"scutil failed: {e}")
                info["DNS Servers"] = "N/A"
            
            # Get interface stats using psutil
            try:
                addresses = psutil.net_if_addrs().get(interface_name, [])
                for addr in addresses:
                    if addr.family == socket.AF_INET:
                        info["IP Address"] = addr.address
                        info["Netmask"] = addr.netmask
                    elif hasattr(psutil, 'AF_LINK') and addr.family == psutil.AF_LINK:
                        info["MAC Address"] = addr.address
                
                stats = psutil.net_if_stats().get(interface_name)
                if stats:
                    info["Status"] = "Up" if stats.isup else "Down"
                    info["Speed"] = f"{stats.speed} Mbps" if stats.speed > 0 else "N/A"
                    info["MTU"] = str(stats.mtu)
            
            except Exception as e:
                logger.debug(f"psutil failed: {e}")
            
            # Set defaults for any missing values
            defaults = {
                "Connection Type": "Unknown",
                "IP Address": "N/A",
                "MAC Address": "N/A",
                "Netmask": "N/A",
                "Speed": "N/A",
                "MTU": "N/A",
                "Status": "N/A",
                "DNS Servers": "N/A",
                "SSID": "N/A",
                "Channel": "N/A",
                "Signal": "N/A",
                "Noise": "N/A",
            }
            
            for key, default_val in defaults.items():
                if key not in info:
                    info[key] = default_val
            
            return info
        
        except Exception as e:
            log_exception(e, context="get_connection_details")
            return {"Error": f"An unexpected error occurred: {e}"}

    def traceroute_test(self, host: str) -> str:
        """Perform a traceroute to a destination host.
        
        Args:
            host: Hostname or IP address to trace
        
        Returns:
            str: Formatted traceroute output or error message
        
        Raises:
            PrivilegeError: If elevated privileges are required
        """
        try:
            if os.geteuid() != 0:
                return "Traceroute requires administrator privileges. Please run with 'sudo'."
            
            output = safe_subprocess_run(
                ["traceroute", "-I", host],
                timeout=45,
                check_command_exists=True,
            )
            return f"--- Traceroute to {host} ---\n{output}"
        
        except CommandNotFoundError:
            return "Traceroute command not found. Please install it or ensure it's in your PATH."
        except Exception as e:
            log_exception(e, context="traceroute_test")
            return format_error_message(e, context=f"Traceroute to {host} failed")

    def network_adapter_info(self) -> str:
        """Get network adapter information using ifconfig.
        
        Returns:
            str: Formatted adapter information or error message
        """
        try:
            return safe_subprocess_run(
                ["ifconfig"],
                timeout=10,
                check_command_exists=False,
            )
        except Exception as e:
            log_exception(e, context="network_adapter_info")
            return format_error_message(e, context="Failed to get adapter info")
