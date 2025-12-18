"""
Port Connectivity Utilities Module

Provides comprehensive port scanning and connectivity testing capabilities,
including TCP probes, service detection, and concurrent port checking.

Author: Network-Triage-Tool Contributors
License: MIT
"""

import socket
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import concurrent.futures
import threading


class PortStatus(Enum):
    """Port status indicators."""
    OPEN = "open"
    CLOSED = "closed"
    FILTERED = "filtered"  # Likely firewall/ACL
    TIMEOUT = "timeout"
    ERROR = "error"


# Common service port mappings
COMMON_SERVICE_PORTS = {
    20: 'FTP-DATA',
    21: 'FTP',
    22: 'SSH',
    23: 'TELNET',
    25: 'SMTP',
    53: 'DNS',
    80: 'HTTP',
    110: 'POP3',
    143: 'IMAP',
    161: 'SNMP',
    179: 'BGP',
    389: 'LDAP',
    443: 'HTTPS',
    445: 'SMB',
    465: 'SMTPS',
    587: 'SMTP-TLS',
    636: 'LDAPS',
    993: 'IMAPS',
    995: 'POP3S',
    1433: 'MSSQL',
    3306: 'MySQL',
    3389: 'RDP',
    5432: 'PostgreSQL',
    5900: 'VNC',
    6379: 'Redis',
    8080: 'HTTP-ALT',
    8443: 'HTTPS-ALT',
    27017: 'MongoDB',
    50000: 'SAP',
}


@dataclass
class PortCheckResult:
    """Result of a single port check."""
    host: str
    port: int
    status: PortStatus
    service_name: Optional[str]
    response_time_ms: float
    error_message: Optional[str] = None
    banner: Optional[str] = None  # Service banner if available

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = asdict(self)
        result['status'] = self.status.value
        return {k: v for k, v in result.items() if v is not None}


def check_port_open(
    host: str,
    port: int,
    timeout: int = 3,
    grab_banner: bool = False
) -> PortCheckResult:
    """
    Check if a single port is open using TCP connection attempt.

    Args:
        host: Hostname or IP address to check
        port: Port number (1-65535)
        timeout: Connection timeout in seconds
        grab_banner: Whether to attempt to read service banner

    Returns:
        PortCheckResult with status and metrics

    Example:
        >>> result = check_port_open('localhost', 22)
        >>> print(result.status.value)
        'open'
    """
    start_time = time.time()
    result = PortCheckResult(
        host=host,
        port=port,
        status=PortStatus.ERROR,
        service_name=COMMON_SERVICE_PORTS.get(port),
        response_time_ms=0,
        error_message=None
    )

    # Validate port
    if not (1 <= port <= 65535):
        result.status = PortStatus.ERROR
        result.error_message = f"Invalid port: {port}"
        return result

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        try:
            # Attempt connection
            sock.connect((host, port))
            result.status = PortStatus.OPEN

            # Optionally grab banner
            if grab_banner:
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    result.banner = banner[:100]  # Limit to 100 chars
                except (socket.timeout, socket.error):
                    pass  # Banner grab optional

        except socket.timeout:
            # Timeout indicates filtered (likely firewall)
            result.status = PortStatus.FILTERED
            result.error_message = f"Connection timeout after {timeout}s"

        except ConnectionRefusedError:
            # Refused indicates port is closed (host responds with RST)
            result.status = PortStatus.CLOSED

        except socket.gaierror as e:
            # Name resolution failed
            result.status = PortStatus.ERROR
            result.error_message = f"DNS resolution failed: {str(e)}"

        except OSError as e:
            # Other OS errors (host unreachable, etc.)
            if 'Network is unreachable' in str(e):
                result.status = PortStatus.FILTERED
            elif 'No route to host' in str(e):
                result.status = PortStatus.FILTERED
            else:
                result.status = PortStatus.ERROR
            result.error_message = str(e)

        except Exception as e:
            result.status = PortStatus.ERROR
            result.error_message = str(e)

        finally:
            sock.close()

    except Exception as e:
        result.status = PortStatus.ERROR
        result.error_message = f"Socket creation error: {str(e)}"

    result.response_time_ms = (time.time() - start_time) * 1000
    return result


def check_multiple_ports(
    host: str,
    ports: List[int],
    timeout: int = 3,
    max_workers: int = 10
) -> List[PortCheckResult]:
    """
    Check multiple ports concurrently.

    Args:
        host: Hostname or IP address
        ports: List of port numbers to check
        timeout: Timeout per port in seconds
        max_workers: Maximum concurrent threads

    Returns:
        List of PortCheckResult objects

    Example:
        >>> results = check_multiple_ports('localhost', [22, 80, 443, 3306])
        >>> open_ports = [r for r in results if r.status == PortStatus.OPEN]
    """
    results = []

    def check_port_wrapper(port: int) -> PortCheckResult:
        return check_port_open(host, port, timeout)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_port_wrapper, port): port for port in ports}

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=timeout + 2)
                results.append(result)
            except Exception as e:
                port = futures[future]
                results.append(PortCheckResult(
                    host=host,
                    port=port,
                    status=PortStatus.ERROR,
                    service_name=COMMON_SERVICE_PORTS.get(port),
                    response_time_ms=(time.time() - time.time()) * 1000,
                    error_message=str(e)
                ))

    # Sort by port number
    results.sort(key=lambda r: r.port)
    return results


def scan_common_ports(
    host: str,
    timeout: int = 3,
    max_workers: int = 10
) -> List[PortCheckResult]:
    """
    Scan all common service ports.

    Args:
        host: Hostname or IP address
        timeout: Timeout per port in seconds
        max_workers: Maximum concurrent threads

    Returns:
        List of PortCheckResult objects for all common ports

    Example:
        >>> results = scan_common_ports('192.168.1.1')
        >>> for result in results:
        ...     if result.status == PortStatus.OPEN:
        ...         print(f"Port {result.port} ({result.service_name}) is open")
    """
    return check_multiple_ports(host, list(COMMON_SERVICE_PORTS.keys()), timeout, max_workers)


def scan_port_range(
    host: str,
    start_port: int = 1,
    end_port: int = 1024,
    timeout: int = 2,
    max_workers: int = 20
) -> List[PortCheckResult]:
    """
    Scan a range of ports (useful for finding unexpected services).

    Args:
        host: Hostname or IP address
        start_port: Starting port number (inclusive)
        end_port: Ending port number (inclusive)
        timeout: Timeout per port in seconds
        max_workers: Maximum concurrent threads

    Returns:
        List of PortCheckResult objects for open ports only

    Note:
        Returns only OPEN ports to reduce output. Use check_multiple_ports
        for detailed results including closed/filtered ports.

    Example:
        >>> results = scan_port_range('192.168.1.100', 1, 1024)
        >>> print(f"Found {len(results)} open ports")
    """
    if not (1 <= start_port <= 65535 and 1 <= end_port <= 65535):
        raise ValueError("Port numbers must be between 1 and 65535")

    if start_port > end_port:
        start_port, end_port = end_port, start_port

    ports = list(range(start_port, end_port + 1))
    all_results = check_multiple_ports(host, ports, timeout, max_workers)

    # Filter to only open ports
    return [r for r in all_results if r.status == PortStatus.OPEN]


def get_service_name(port: int) -> str:
    """
    Get service name for a port number.

    Args:
        port: Port number

    Returns:
        Service name or "Unknown" if not in common services

    Example:
        >>> get_service_name(22)
        'SSH'
    """
    return COMMON_SERVICE_PORTS.get(port, 'Unknown')


def get_common_service_ports() -> Dict[int, str]:
    """
    Return dictionary of all common service ports.

    Returns:
        Dictionary mapping port number to service name

    Example:
        >>> ports = get_common_service_ports()
        >>> print(f"Monitoring {len(ports)} common ports")
    """
    return COMMON_SERVICE_PORTS.copy()


def summarize_port_scan(results: List[PortCheckResult]) -> Dict[str, Any]:
    """
    Generate summary statistics from port scan results.

    Args:
        results: List of PortCheckResult objects

    Returns:
        Dictionary with summary statistics

    Example:
        >>> results = check_multiple_ports('localhost', [22, 80, 443, 3306])
        >>> summary = summarize_port_scan(results)
        >>> print(summary['open_count'])
    """
    open_ports = [r for r in results if r.status == PortStatus.OPEN]
    closed_ports = [r for r in results if r.status == PortStatus.CLOSED]
    filtered_ports = [r for r in results if r.status == PortStatus.FILTERED]
    timeout_ports = [r for r in results if r.status == PortStatus.TIMEOUT]
    error_ports = [r for r in results if r.status == PortStatus.ERROR]

    response_times = [r.response_time_ms for r in results if r.response_time_ms > 0]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    return {
        'total_scanned': len(results),
        'open_count': len(open_ports),
        'closed_count': len(closed_ports),
        'filtered_count': len(filtered_ports),
        'timeout_count': len(timeout_ports),
        'error_count': len(error_ports),
        'open_ports': [(r.port, r.service_name) for r in open_ports],
        'avg_response_time_ms': avg_response_time,
        'min_response_time_ms': min(response_times) if response_times else 0,
        'max_response_time_ms': max(response_times) if response_times else 0,
    }


if __name__ == '__main__':
    # Example usage
    print("\n=== Single Port Check ===")
    result = check_port_open('localhost', 22)
    print(f"Host: {result.host}")
    print(f"Port: {result.port} ({result.service_name})")
    print(f"Status: {result.status.value}")
    print(f"Response time: {result.response_time_ms:.2f}ms")

    print("\n=== Multiple Common Ports ===")
    results = check_multiple_ports('localhost', [22, 80, 443, 3306, 5432])
    summary = summarize_port_scan(results)
    print(f"Total scanned: {summary['total_scanned']}")
    print(f"Open: {summary['open_count']}")
    print(f"Closed: {summary['closed_count']}")
    print(f"Filtered: {summary['filtered_count']}")
    if summary['open_ports']:
        print(f"Open ports: {summary['open_ports']}")
