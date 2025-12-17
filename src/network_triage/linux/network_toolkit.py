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
        # TODO: Implement using:
        # - lsb_release -ds for distro
        # - lsb_release -rs for version
        # - hostname for hostname
        # - uname -r for kernel
        # - uname -m for architecture
      try:                    ← ADD THIS (replace the 'pass' line)
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
        # TODO: Implement using:
        # - ip route to find default gateway
        # - ip addr to find primary IP
        # - safe_http_request for public IP
        pass

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
        # TODO: Implement using:
        # - ip link show for MAC and MTU
        # - ip addr show for IP addresses
        # - ethtool for speed
        # - ip route for gateway
        # - iwconfig for wireless info (if applicable)
        pass

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
        # TODO: Implement using:
        # - ip link show for all interfaces
        # - ip addr show for addresses per interface
        # - ethtool for detailed info
        pass

    def traceroute_test(self, destination: str = "8.8.8.8") -> dict:
        """Perform a traceroute test to a destination.

        Traces the network path to a destination host, showing each hop
        and round-trip times.

        Uses command:
        - traceroute for path tracing

        Args:
            destination: Target hostname or IP address (default: 8.8.8.8 Google DNS)

        Returns:
            dict: Traceroute results with keys:
                - Destination: Target host
                - Hops: List of hops with IP, hostname, and latency
                - Success: Whether traceroute completed
                - Message: Status or error message

        Raises:
            NetworkCommandError: If traceroute command fails
            CommandNotFoundError: If traceroute not installed

        Example:
            >>> result = toolkit.traceroute_test('google.com')
            >>> print(f"Hops: {len(result['Hops'])}")
            'Hops: 12'
        """
        # TODO: Implement using:
        # - traceroute command
        # - Parse output for hops
        # - Extract IP, hostname, and latency
        pass


# TODO: Helper functions for Linux-specific parsing
# - parse_ip_output(): Parse 'ip' command output
# - parse_ethtool_output(): Parse 'ethtool' command output
# - parse_iwconfig_output(): Parse 'iwconfig' command output
# - parse_lsb_release(): Parse 'lsb_release' command output
# - get_primary_interface(): Find primary network interface
# - is_wireless_interface(): Check if interface is wireless
