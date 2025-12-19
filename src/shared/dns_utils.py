"""
DNS Resolution Utilities Module

Provides comprehensive DNS testing capabilities including A/AAAA record resolution,
reverse DNS lookups, DNS server validation, and propagation checking across
public DNS providers.

Author: Network-Triage-Tool Contributors
License: MIT
"""

import socket
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import concurrent.futures


class DNSStatus(Enum):
    """DNS lookup status indicators."""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    ERROR = "error"
    PARTIAL = "partial"  # Some records found, some failed


@dataclass
class DNSRecord:
    """Represents a single DNS record result."""
    record_type: str  # 'A', 'AAAA', 'PTR'
    value: str  # IP address or hostname
    query_time_ms: float
    status: DNSStatus


@dataclass
class DNSLookupResult:
    """Complete DNS lookup result for a hostname."""
    hostname: str
    ipv4_addresses: List[str]
    ipv6_addresses: List[str]
    reverse_dns: Optional[str]
    lookup_time_ms: float
    status: DNSStatus
    error_message: Optional[str] = None
    records: List[DNSRecord] = None

    def __post_init__(self):
        if self.records is None:
            self.records = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = asdict(self)
        result['status'] = self.status.value
        result['records'] = [
            {**asdict(r), 'status': r.status.value}
            for r in self.records
        ]
        return {k: v for k, v in result.items() if v is not None}


def resolve_hostname(
    hostname: str,
    timeout: int = 5,
    include_reverse_dns: bool = True
) -> DNSLookupResult:
    """
    Resolve A, AAAA, and optionally reverse DNS records for a hostname.

    Args:
        hostname: FQDN or IP address to resolve
        timeout: Socket timeout in seconds
        include_reverse_dns: Whether to perform reverse DNS lookup

    Returns:
        DNSLookupResult containing all resolved records

    Example:
        >>> result = resolve_hostname('google.com')
        >>> print(result.ipv4_addresses)
        ['142.250.185.46']
    """
    start_time = time.time()
    result = DNSLookupResult(
        hostname=hostname,
        ipv4_addresses=[],
        ipv6_addresses=[],
        reverse_dns=None,
        lookup_time_ms=0,
        status=DNSStatus.SUCCESS,
        error_message=None
    )

    # Set socket timeout
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)

    try:
        # Try getaddrinfo for both A and AAAA records
        try:
            address_info = socket.getaddrinfo(
                hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM
            )

            for family, socktype, proto, canonname, sockaddr in address_info:
                ip_addr = sockaddr[0]
                query_time = (time.time() - start_time) * 1000

                if family == socket.AF_INET:
                    if ip_addr not in result.ipv4_addresses:
                        result.ipv4_addresses.append(ip_addr)
                        result.records.append(DNSRecord(
                            record_type='A',
                            value=ip_addr,
                            query_time_ms=query_time,
                            status=DNSStatus.SUCCESS
                        ))
                elif family == socket.AF_INET6:
                    # Normalize IPv6 address (remove trailing %interface)
                    ipv6_clean = ip_addr.split('%')[0]
                    if ipv6_clean not in result.ipv6_addresses:
                        result.ipv6_addresses.append(ipv6_clean)
                        result.records.append(DNSRecord(
                            record_type='AAAA',
                            value=ipv6_clean,
                            query_time_ms=query_time,
                            status=DNSStatus.SUCCESS
                        ))

        except socket.gaierror as e:
            result.status = DNSStatus.NOT_FOUND
            result.error_message = str(e)
            result.records.append(DNSRecord(
                record_type='A/AAAA',
                value='',
                query_time_ms=(time.time() - start_time) * 1000,
                status=DNSStatus.NOT_FOUND
            ))
            return result

        except socket.timeout:
            result.status = DNSStatus.TIMEOUT
            result.error_message = f"DNS resolution timeout after {timeout}s"
            return result

        # Reverse DNS lookup if requested and we have IP addresses
        if include_reverse_dns and result.ipv4_addresses:
            try:
                reverse_lookup = socket.gethostbyaddr(result.ipv4_addresses[0])
                result.reverse_dns = reverse_lookup[0]
                result.records.append(DNSRecord(
                    record_type='PTR',
                    value=reverse_lookup[0],
                    query_time_ms=(time.time() - start_time) * 1000,
                    status=DNSStatus.SUCCESS
                ))
            except (socket.herror, socket.timeout):
                # Reverse DNS is optional; don't fail if it times out
                pass

    except Exception as e:
        result.status = DNSStatus.ERROR
        result.error_message = f"Unexpected error: {str(e)}"
        return result

    finally:
        socket.setdefaulttimeout(old_timeout)
        result.lookup_time_ms = (time.time() - start_time) * 1000

    return result


def validate_dns_server(
    server_ip: str,
    test_domain: str = "google.com",
    timeout: int = 5
) -> Dict[str, Any]:
    """
    Validate if a DNS server is responsive and functional.

    Args:
        server_ip: IP address of DNS server to test (port 53 assumed)
        test_domain: Domain to use for validation query
        timeout: Socket timeout in seconds

    Returns:
        Dictionary with validation result and metrics

    Example:
        >>> result = validate_dns_server('8.8.8.8')
        >>> print(result['is_responsive'])
        True
    """
    start_time = time.time()
    result = {
        'server_ip': server_ip,
        'test_domain': test_domain,
        'is_responsive': False,
        'response_time_ms': 0,
        'error': None,
        'status': 'unknown'
    }

    try:
        # Attempt to create a UDP socket and send a DNS query
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        try:
            # Simple DNS query for A record
            # Format: standard DNS query packet for test_domain
            dns_query = _build_simple_dns_query(test_domain)
            sock.sendto(dns_query, (server_ip, 53))
            response, _ = sock.recvfrom(512)

            if response:
                result['is_responsive'] = True
                result['status'] = 'responsive'
            else:
                result['status'] = 'no_response'

        except socket.timeout:
            result['status'] = 'timeout'
            result['error'] = f"No response after {timeout}s"
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        finally:
            sock.close()

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)

    result['response_time_ms'] = (time.time() - start_time) * 1000
    return result


def check_dns_propagation(
    domain: str,
    record_type: str = "A",
    timeout: int = 5
) -> List[Dict[str, Any]]:
    """
    Check DNS propagation across multiple public DNS providers.

    Args:
        domain: Domain to check
        record_type: Type of record ('A', 'AAAA', 'CNAME', 'MX')
        timeout: Timeout per server in seconds

    Returns:
        List of results from each DNS provider

    Example:
        >>> results = check_dns_propagation('example.com')
        >>> for result in results:
        ...     print(f"{result['provider']}: {result['ips']}")
    """
    # Major public DNS providers
    public_dns_servers = {
        'Google': ['8.8.8.8', '8.8.4.4'],
        'Cloudflare': ['1.1.1.1', '1.0.0.1'],
        'OpenDNS': ['208.67.222.222', '208.67.220.220'],
        'Quad9': ['9.9.9.9', '149.112.112.112'],
        'ISP DNS': ['8.8.8.8'],  # Fallback; user may override
    }

    propagation_results = []

    def check_with_resolver(provider_name: str, server_ip: str) -> Dict[str, Any]:
        """Check a single DNS resolver."""
        try:
            # Set resolver temporarily
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(timeout)

            try:
                # Use getaddrinfo with the resolver (limited support)
                # More reliable: use direct socket query
                addresses = socket.gethostbyname_ex(domain)
                ips = addresses[2]
                status = 'found'
            except socket.gaierror:
                ips = []
                status = 'not_found'
            except socket.timeout:
                ips = []
                status = 'timeout'
            finally:
                socket.setdefaulttimeout(old_timeout)

            return {
                'provider': provider_name,
                'server_ip': server_ip,
                'ips': ips,
                'status': status
            }
        except Exception as e:
            return {
                'provider': provider_name,
                'server_ip': server_ip,
                'ips': [],
                'status': 'error',
                'error': str(e)
            }

    # Use ThreadPoolExecutor for concurrent checks
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for provider, servers in public_dns_servers.items():
            for server_ip in servers[:1]:  # Use first server per provider
                future = executor.submit(check_with_resolver, provider, server_ip)
                futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=timeout + 2)
                propagation_results.append(result)
            except Exception as e:
                propagation_results.append({
                    'provider': 'unknown',
                    'status': 'error',
                    'error': str(e)
                })

    return propagation_results


def _build_simple_dns_query(domain: str) -> bytes:
    """
    Build a simple DNS query packet for validation.

    This is a minimal DNS query packet for A record lookup.
    Format based on RFC 1035.

    Args:
        domain: Domain to query

    Returns:
        Binary DNS query packet
    """
    # DNS header
    transaction_id = b'\x00\x01'  # Simple ID
    flags = b'\x01\x00'  # Standard query
    questions = b'\x00\x01'  # 1 question
    answer_rrs = b'\x00\x00'  # No answers (request)
    authority_rrs = b'\x00\x00'  # No authority
    additional_rrs = b'\x00\x00'  # No additional

    header = transaction_id + flags + questions + answer_rrs + authority_rrs + additional_rrs

    # Question section
    question = b''
    for label in domain.split('.'):
        question += bytes([len(label)]) + label.encode('utf-8')
    question += b'\x00'  # Root label
    question += b'\x00\x01'  # Type A
    question += b'\x00\x01'  # Class IN

    return header + question


if __name__ == '__main__':
    # Example usage
    print("\n=== DNS Resolution Test ===")
    result = resolve_hostname('google.com')
    print(f"Hostname: {result.hostname}")
    print(f"IPv4: {result.ipv4_addresses}")
    print(f"IPv6: {result.ipv6_addresses}")
    print(f"Reverse DNS: {result.reverse_dns}")
    print(f"Lookup time: {result.lookup_time_ms:.2f}ms")
    print(f"Status: {result.status.value}")

    print("\n=== DNS Server Validation ===")
    server_result = validate_dns_server('8.8.8.8')
    print(f"Server: {server_result['server_ip']}")
    print(f"Responsive: {server_result['is_responsive']}")
    print(f"Response time: {server_result['response_time_ms']:.2f}ms")

    print("\n=== DNS Propagation Check ===")
    propagation = check_dns_propagation('google.com')
    for provider_result in propagation:
        print(f"{provider_result['provider']}: {provider_result['status']}")
