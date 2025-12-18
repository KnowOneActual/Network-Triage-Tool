"""Linux network toolkit - Phase 2 implementation.

Provides Linux-specific implementations of network diagnostics
using the same interface as the macOS toolkit for cross-platform
consistency.

Uses Linux commands:
- ip: Network configuration
- ethtool: Interface statistics
- iwconfig: Wireless configuration
- lsb_release: OS information
- uname: System information
- curl/wget: HTTP requests
"""

import logging
import re
from ..exceptions import (
    NetworkTriageException,
    NetworkCommandError,
    NetworkTimeoutError,
    CommandNotFoundError,
    NetworkConnectivityError,
)
from ..utils import safe_subprocess_run, safe_http_request, safe_socket_operation

logger = logging.getLogger(__name__)


class NetworkTriageToolkit:
    """Linux-specific network diagnostic toolkit.

    Implements the same methods as macOS toolkit but uses Linux
    commands (ip, ethtool, iwconfig, etc.) for equivalent functionality.

    This ensures cross-platform consistency while leveraging platform-specific
    tools for best results.
    """

    def __init__(self):
        """Initialize the Linux network toolkit."""
        self.logger = logging.getLogger(__name__)

    def get_system_info(self) -> dict:
        """Get system information (OS, hostname, etc).

        Retrieves system-level information using Linux commands:
        - lsb_release for distro name and version
        - uname for kernel version
        - hostname for system hostname

        Returns:
            dict: System information with keys:
                - OS: Linux distribution name and version
                - Hostname: System hostname
                - Kernel: Linux kernel version
                - Arch: System architecture

        Raises:
            NetworkTriageException: If system info cannot be retrieved

        Example:
            >>> toolkit = NetworkTriageToolkit()
            >>> info = toolkit.get_system_info()
            >>> print(info['OS'])
            'Ubuntu 22.04.1 LTS'
        """
        try:
            # Get distro info
            distro = safe_subprocess_run(['lsb_release', '-ds'], timeout=5)
            kernel = safe_subprocess_run(['uname', '-r'], timeout=5)
            hostname = safe_subprocess_run(['hostname'], timeout=5)
            arch = safe_subprocess_run(['uname', '-m'], timeout=5)
            
            return {
                'OS': distro.strip(),
                'Hostname': hostname.strip(),
                'Kernel': kernel.strip(),
                'Arch': arch.strip(),
            }
        except CommandNotFoundError as e:
            logger.warning(f"System info command not found: {e}")
            # Graceful fallback
            return {
                'OS': 'Linux',
                'Hostname': 'Unknown',
                'Kernel': 'Unknown',
                'Arch': 'Unknown',
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            raise NetworkCommandError(f"Failed to get system info: {e}")

    def get_ip_info(self) -> dict:
        """Get IP configuration (internal and public IP).

        Retrieves IP addresses using:
        - ip addr for internal IP (from primary interface)
        - HTTP request to ipinfo.io for public IP

        Returns:
            dict: IP information with keys:
                - Internal IP: Local IP address
                - Public IP: External IP address
                - Gateway: Default gateway

        Raises:
            NetworkConnectivityError: If IP info cannot be retrieved

        Example:
            >>> info = toolkit.get_ip_info()
            >>> print(info['Public IP'])
            '203.0.113.42'
        """
        try:
            # Find default gateway and primary interface
            route_output = safe_subprocess_run(['ip', 'route', 'show', 'default'], timeout=5)
            
            # Parse to extract primary interface (usually second field)
            parts = route_output.split()
            if len(parts) >= 5:
                interface = parts[4]
            else:
                interface = 'eth0'  # fallback
            
            # Get internal IP from primary interface
            ip_output = safe_subprocess_run(['ip', '-4', 'addr', 'show', interface], timeout=5)
            
            # Extract IP using regex
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_output)
            internal_ip = ip_match.group(1) if ip_match else 'Unknown'
            
            # Extract gateway from route output
            gateway = parts[2] if len(parts) >= 3 else 'Unknown'
            
            # Get public IP via HTTP
            try:
                public_data = safe_http_request('https://api.ipify.org?format=json', timeout=5)
                public_ip = public_data.get('ip', 'Unavailable')
            except Exception as e:
                logger.warning(f"Could not get public IP: {e}")
                public_ip = 'Unavailable'
            
            return {
                'Internal IP': internal_ip,
                'Public IP': public_ip,
                'Gateway': gateway,
            }
        except Exception as e:
            logger.error(f"Failed to get IP info: {e}")
            return {
                'Internal IP': 'Unknown',
                'Public IP': 'Unavailable',
                'Gateway': 'Unknown',
            }

    def get_connection_details(self) -> dict:
        """Get detailed connection information.

        Retrieves comprehensive connection details including:
        - Interface name, IP, MAC address
        - Interface speed and MTU
        - WiFi details (SSID, signal strength) if connected

        Uses commands:
        - ip link for MAC and MTU
        - ip addr for IP addresses
        - ethtool for speed information
        - iwconfig for wireless details

        Returns:
            dict: Connection details (varies based on connection type)
                Standard keys:
                - Interface: Interface name
                - IP Address: IPv4 address
                - MAC Address: Hardware address
                - Netmask: Subnet mask
                - Speed: Link speed
                - MTU: Maximum transmission unit
                - Gateway: Default gateway

        Example:
            >>> details = toolkit.get_connection_details()
            >>> print(details['Interface'])
            'eth0'
        """
        try:
            # Get primary interface
            route_output = safe_subprocess_run(['ip', 'route', 'show', 'default'], timeout=5)
            parts = route_output.split()
            interface = parts[4] if len(parts) >= 5 else 'eth0'
            
            # Get IP and netmask
            addr_output = safe_subprocess_run(['ip', '-4', 'addr', 'show', interface], timeout=5)
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', addr_output)
            ip_addr = ip_match.group(1) if ip_match else 'Unknown'
            netmask_bits = ip_match.group(2) if ip_match else '24'
            
            # Convert netmask bits to dotted notation
            def bits_to_netmask(bits):
                try:
                    bits = int(bits)
                    mask = (0xffffffff >> (32 - bits)) << (32 - bits)
                    return '.'.join([str((mask >> (i << 3)) & 0xff) for i in range(4)[::-1]])
                except:
                    return '255.255.255.0'
            
            netmask = bits_to_netmask(netmask_bits)
            
            # Get MAC address and MTU
            link_output = safe_subprocess_run(['ip', 'link', 'show', interface], timeout=5)
            mac_match = re.search(r'link/ether ([0-9a-f:]+)', link_output)
            mac_addr = mac_match.group(1) if mac_match else 'Unknown'
            
            mtu_match = re.search(r'mtu (\d+)', link_output)
            mtu = mtu_match.group(1) if mtu_match else 'Unknown'
            
            # Get gateway
            gateway = parts[2] if len(parts) >= 3 else 'Unknown'
            
            # Get speed using ethtool
            try:
                ethtool_output = safe_subprocess_run(['ethtool', interface], timeout=5)
                speed_match = re.search(r'Speed: (\d+Mb/s)', ethtool_output)
                speed = speed_match.group(1) if speed_match else 'Unknown'
            except CommandNotFoundError:
                speed = 'Unknown (ethtool not installed)'
            except Exception as e:
                logger.warning(f"Could not get speed: {e}")
                speed = 'Unknown'
            
            # Check if wireless and get WiFi details
            wifi_details = {}
            try:
                iwconfig_output = safe_subprocess_run(['iwconfig', interface], timeout=5)
                # Check if it's a wireless interface (iwconfig succeeds and doesn't show "no wireless")
                if 'no wireless extensions' not in iwconfig_output.lower():
                    # Extract SSID
                    ssid_match = re.search(r'ESSID:"([^"]+)"', iwconfig_output)
                    if ssid_match:
                        wifi_details['SSID'] = ssid_match.group(1)
                    
                    # Extract signal strength
                    signal_match = re.search(r'Signal level[=:](^\s]+)', iwconfig_output)
                    if signal_match:
                        wifi_details['Signal Strength'] = signal_match.group(1)
            except CommandNotFoundError:
                pass  # iwconfig not installed, skip wireless info
            except Exception as e:
                logger.debug(f"Could not get WiFi details: {e}")
            
            result = {
                'Interface': interface,
                'IP Address': ip_addr,
                'Netmask': netmask,
                'MAC Address': mac_addr,
                'Speed': speed,
                'MTU': mtu,
                'Gateway': gateway,
            }
            
            # Add WiFi details if available
            if wifi_details:
                result.update(wifi_details)
            
            return result
        except Exception as e:
            logger.error(f"Failed to get connection details: {e}")
            return {
                'Interface': 'Unknown',
                'IP Address': 'Unknown',
                'MAC Address': 'Unknown',
                'Netmask': 'Unknown',
                'Speed': 'Unknown',
                'MTU': 'Unknown',
                'Gateway': 'Unknown',
            }

    def network_adapter_info(self) -> dict:
        """Get network adapter information.

        Retrieves a list of all network interfaces with their status,
        type, and configuration.

        Uses commands:
        - ip link show for interface status and type
        - ip addr show for address information
        - ethtool for detailed statistics

        Returns:
            dict: Network adapter details with interface names as keys.
                Each adapter contains:
                - Status: up/down
                - Type: loopback, ethernet, wireless, etc.
                - IP: IPv4 address if configured
                - MAC: Hardware address
                - MTU: Maximum transmission unit

        Example:
            >>> adapters = toolkit.network_adapter_info()
            >>> print(adapters['eth0']['Status'])
            'up'
        """
        try:
            adapters = {}
            
            # Get all interfaces using 'ip link show'
            link_output = safe_subprocess_run(['ip', 'link', 'show'], timeout=5)
            
            # Parse each interface line (format: "<number>: <name>: <flags>...")
            for line in link_output.split('\n'):
                # Look for interface lines (start with digit)
                if line and line[0].isdigit():
                    # Extract interface name and status
                    match = re.match(r'\d+: ([^:]+):', line)
                    if match:
                        iface_name = match.group(1)
                        
                        # Determine if interface is up or down
                        status = 'up' if 'UP' in line else 'down'
                        
                        # Determine interface type
                        iface_type = 'unknown'
                        if 'loopback' in line.lower():
                            iface_type = 'loopback'
                        elif 'link/ether' in line.lower():
                            iface_type = 'ethernet'
                        
                        # Get MAC address and MTU for this interface
                        try:
                            iface_link_output = safe_subprocess_run(['ip', 'link', 'show', iface_name], timeout=5)
                            mac_match = re.search(r'link/ether ([0-9a-f:]+)', iface_link_output)
                            mac = mac_match.group(1) if mac_match else 'N/A'
                            
                            mtu_match = re.search(r'mtu (\d+)', iface_link_output)
                            mtu = mtu_match.group(1) if mtu_match else 'Unknown'
                        except Exception as e:
                            logger.debug(f"Could not get details for {iface_name}: {e}")
                            mac = 'N/A'
                            mtu = 'Unknown'
                        
                        # Get IP address for this interface
                        ip_addr = None
                        try:
                            addr_output = safe_subprocess_run(['ip', '-4', 'addr', 'show', iface_name], timeout=5)
                            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', addr_output)
                            if ip_match:
                                ip_addr = ip_match.group(1)
                        except Exception as e:
                            logger.debug(f"Could not get IP for {iface_name}: {e}")
                        
                        # Check if wireless
                        try:
                            iwconfig_output = safe_subprocess_run(['iwconfig', iface_name], timeout=5)
                            if 'no wireless extensions' not in iwconfig_output.lower():
                                iface_type = 'wireless'
                        except CommandNotFoundError:
                            pass  # iwconfig not available
                        except Exception:
                            pass  # Interface not wireless
                        
                        # Store adapter info
                        adapters[iface_name] = {
                            'Status': status,
                            'Type': iface_type,
                            'MAC': mac,
                            'MTU': mtu,
                        }
                        
                        if ip_addr:
                            adapters[iface_name]['IP'] = ip_addr
            
            return adapters if adapters else {'error': 'No interfaces found'}
        except Exception as e:
            logger.error(f"Failed to get network adapter info: {e}")
            return {'error': f'Failed to get adapter info: {e}'}

    def traceroute_test(self, destination: str = "8.8.8.8") -> dict:
    ...
    try:
        traceroute_output = safe_subprocess_run(
            ['traceroute', '-m', '30', destination],
            timeout=30,
        )
        # parse output, build hops, etc.
        ...
        return {
            'Destination': destination,
            'Hops': hops,
            'Success': len(hops) > 0,
            'Message': f'Traceroute completed with {len(hops)} hops',
        }

    except CommandNotFoundError:
        logger.error("traceroute command not found")
        # CI-friendly graceful fallback:
        return {
            'Destination': destination,
            'Hops': [],
            'Success': False,
            'Message': "traceroute command not installed. Please install traceroute package.",
        }

    except NetworkTimeoutError:
        logger.warning(f"Traceroute to {destination} timed out")
        return {
            'Destination': destination,
            'Hops': [],
            'Success': False,
            'Message': f'Traceroute to {destination} timed out',
        }

    except Exception as e:
        logger.error(f"Failed to run traceroute: {e}")
        return {
            'Destination': destination,
            'Hops': [],
            'Success': False,
            'Message': f'Traceroute failed: {e}',
        }



# TODO: Helper functions for Linux-specific parsing
# - parse_ip_output(): Parse 'ip' command output
# - parse_ethtool_output(): Parse 'ethtool' command output
# - parse_iwconfig_output(): Parse 'iwconfig' command output
# - parse_lsb_release(): Parse 'lsb_release' command output
# - get_primary_interface(): Find primary network interface
# - is_wireless_interface(): Check if interface is wireless
