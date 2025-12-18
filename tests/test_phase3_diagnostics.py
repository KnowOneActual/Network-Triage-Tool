"""
Unit tests for Phase 3 Advanced Diagnostics modules.

Tests DNS utilities, port connectivity, and latency measurement functions.
Uses mocking to avoid network calls and ensure fast test execution.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import statistics

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shared.dns_utils import (
    resolve_hostname,
    validate_dns_server,
    check_dns_propagation,
    DNSStatus,
    DNSLookupResult,
)
from shared.port_utils import (
    check_port_open,
    check_multiple_ports,
    scan_common_ports,
    scan_port_range,
    get_service_name,
    summarize_port_scan,
    PortStatus,
)
from shared.latency_utils import (
    ping_statistics,
    mtr_style_trace,
    _parse_ping_output,
    LatencyStatus,
    PingStatistics,
)


class TestDNSUtils(unittest.TestCase):
    """Test suite for DNS utilities module."""

    @patch('shared.dns_utils.socket')
    def test_resolve_hostname_success(self, mock_socket):
        """Test successful hostname resolution."""
        # Mock getaddrinfo to return A and AAAA records
        mock_socket.getaddrinfo.return_value = [
            (2, 1, 6, '', ('142.250.185.46', 0)),  # IPv4
            (10, 1, 6, '', ('2607:f8b0:4004:809::200e', 0)),  # IPv6
        ]
        mock_socket.AF_INET = 2
        mock_socket.AF_INET6 = 10
        mock_socket.SOCK_STREAM = 1
        mock_socket.AF_UNSPEC = 0
        mock_socket.gaierror = Exception
        mock_socket.herror = Exception
        mock_socket.timeout = Exception

        result = resolve_hostname('google.com')

        self.assertEqual(result.hostname, 'google.com')
        self.assertEqual(len(result.ipv4_addresses), 1)
        self.assertEqual(len(result.ipv6_addresses), 1)
        self.assertEqual(result.status, DNSStatus.SUCCESS)

    @patch('shared.dns_utils.socket')
    def test_resolve_hostname_not_found(self, mock_socket):
        """Test hostname not found scenario."""
        mock_socket.getaddrinfo.side_effect = Exception("Name or service not known")
        mock_socket.gaierror = Exception
        mock_socket.AF_UNSPEC = 0
        mock_socket.SOCK_STREAM = 1

        result = resolve_hostname('invalid-hostname-12345.com')

        self.assertEqual(result.status, DNSStatus.NOT_FOUND)
        self.assertEqual(len(result.ipv4_addresses), 0)
        self.assertIsNotNone(result.error_message)

    @patch('shared.dns_utils.socket')
    def test_resolve_hostname_timeout(self, mock_socket):
        """Test DNS resolution timeout."""
        mock_socket.getaddrinfo.side_effect = Exception("DNS query timed out")
        mock_socket.gaierror = Exception
        mock_socket.timeout = Exception
        mock_socket.AF_UNSPEC = 0
        mock_socket.SOCK_STREAM = 1

        result = resolve_hostname('slow-dns.example.com', timeout=1)

        # Should handle timeout gracefully
        self.assertIn(result.status, [DNSStatus.TIMEOUT, DNSStatus.NOT_FOUND, DNSStatus.ERROR])

    @patch('shared.dns_utils.socket')
    def test_validate_dns_server_responsive(self, mock_socket):
        """Test DNS server validation - responsive server."""
        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.recvfrom.return_value = (b'\x00\x01\x81\x80' + b'\x00' * 8, ('8.8.8.8', 53))

        result = validate_dns_server('8.8.8.8')

        self.assertTrue(result['is_responsive'])
        self.assertEqual(result['status'], 'responsive')
        self.assertEqual(result['server_ip'], '8.8.8.8')

    @patch('shared.dns_utils.socket')
    def test_validate_dns_server_timeout(self, mock_socket):
        """Test DNS server validation - timeout."""
        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.recvfrom.side_effect = Exception("Socket timeout")
        mock_sock_instance.timeout = Exception

        result = validate_dns_server('invalid-server.local', timeout=1)

        self.assertFalse(result['is_responsive'])
        self.assertIn(result['status'], ['timeout', 'error', 'no_response'])

    @patch('shared.dns_utils.socket.gethostbyname_ex')
    def test_check_dns_propagation(self, mock_gethostbyname):
        """Test DNS propagation check across providers."""
        mock_gethostbyname.return_value = ('google.com', [], ['142.250.185.46'])

        results = check_dns_propagation('google.com')

        self.assertGreater(len(results), 0)
        # Check that results have expected structure
        for result in results:
            self.assertIn('provider', result)
            self.assertIn('status', result)
            self.assertIn('ips', result)


class TestPortUtils(unittest.TestCase):
    """Test suite for port utilities module."""

    @patch('shared.port_utils.socket')
    def test_check_port_open(self, mock_socket):
        """Test port check - port is open."""
        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None

        result = check_port_open('localhost', 22)

        self.assertEqual(result.status, PortStatus.OPEN)
        self.assertEqual(result.port, 22)
        self.assertEqual(result.service_name, 'SSH')
        self.assertGreaterEqual(result.response_time_ms, 0)

    @patch('shared.port_utils.socket')
    def test_check_port_closed(self, mock_socket):
        """Test port check - port is closed."""
        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.side_effect = ConnectionRefusedError()

        result = check_port_open('localhost', 54321)

        self.assertEqual(result.status, PortStatus.CLOSED)

    @patch('shared.port_utils.socket')
    def test_check_port_timeout(self, mock_socket):
        """Test port check - timeout (filtered port)."""
        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.side_effect = Exception("Socket timeout")
        mock_sock_instance.timeout = Exception

        result = check_port_open('10.255.255.1', 22, timeout=1)

        self.assertEqual(result.status, PortStatus.FILTERED)

    @patch('shared.port_utils.socket')
    def test_check_port_invalid_port(self, mock_socket):
        """Test port check - invalid port number."""
        result = check_port_open('localhost', 99999)

        self.assertEqual(result.status, PortStatus.ERROR)
        self.assertIsNotNone(result.error_message)

    @patch('shared.port_utils.check_port_open')
    def test_check_multiple_ports(self, mock_check_port):
        """Test concurrent port checking."""
        # Mock results for multiple ports
        results = [
            type('obj', (object,), {'port': 22, 'status': PortStatus.OPEN, 'service_name': 'SSH'}),
            type('obj', (object,), {'port': 80, 'status': PortStatus.CLOSED, 'service_name': 'HTTP'}),
        ]
        mock_check_port.side_effect = results

        result = check_multiple_ports('localhost', [22, 80])

        # Note: Since we mocked check_port_open, we're testing the threading logic
        self.assertEqual(len(result), 2)

    def test_get_service_name(self):
        """Test service name lookup."""
        self.assertEqual(get_service_name(22), 'SSH')
        self.assertEqual(get_service_name(80), 'HTTP')
        self.assertEqual(get_service_name(443), 'HTTPS')
        self.assertEqual(get_service_name(99999), 'Unknown')

    def test_summarize_port_scan(self):
        """Test port scan result summarization."""
        # Create mock results
        open_result = type('obj', (object,), {
            'port': 22,
            'status': PortStatus.OPEN,
            'response_time_ms': 15.5,
            'service_name': 'SSH'
        })
        closed_result = type('obj', (object,), {
            'port': 23,
            'status': PortStatus.CLOSED,
            'response_time_ms': 2.1,
            'service_name': 'TELNET'
        })

        results = [open_result, closed_result]
        summary = summarize_port_scan(results)

        self.assertEqual(summary['total_scanned'], 2)
        self.assertEqual(summary['open_count'], 1)
        self.assertEqual(summary['closed_count'], 1)
        self.assertGreater(summary['avg_response_time_ms'], 0)


class TestLatencyUtils(unittest.TestCase):
    """Test suite for latency utilities module."""

    def test_parse_ping_output_linux(self):
        """Test ping output parsing for Linux."""
        ping_output = """
PING google.com (142.250.185.46) 56(84) bytes of data.
64 bytes from lax17s28-in-f14.1e100.net (142.250.185.46): icmp_seq=1 ttl=119 time=15.123 ms
64 bytes from lax17s28-in-f14.1e100.net (142.250.185.46): icmp_seq=2 ttl=119 time=14.856 ms
64 bytes from lax17s28-in-f14.1e100.net (142.250.185.46): icmp_seq=3 ttl=119 time=16.234 ms
        """

        rtt_values = _parse_ping_output(ping_output, 'Linux')

        self.assertEqual(len(rtt_values), 3)
        self.assertAlmostEqual(rtt_values[0], 15.123, places=2)
        self.assertAlmostEqual(rtt_values[1], 14.856, places=2)
        self.assertAlmostEqual(rtt_values[2], 16.234, places=2)

    def test_parse_ping_output_windows(self):
        """Test ping output parsing for Windows."""
        ping_output = """
Reply from 8.8.8.8: bytes=32 time=20ms TTL=119
Reply from 8.8.8.8: bytes=32 time=19ms TTL=119
Reply from 8.8.8.8: bytes=32 time=21ms TTL=119
        """

        rtt_values = _parse_ping_output(ping_output, 'Windows')

        self.assertEqual(len(rtt_values), 3)
        self.assertEqual(rtt_values[0], 20.0)
        self.assertEqual(rtt_values[1], 19.0)
        self.assertEqual(rtt_values[2], 21.0)

    @patch('shared.latency_utils.subprocess.Popen')
    def test_ping_statistics_success(self, mock_popen):
        """Test ping statistics calculation."""
        ping_output = """
PING google.com (142.250.185.46) 56(84) bytes of data.
64 bytes from google.com: icmp_seq=1 ttl=119 time=15.0 ms
64 bytes from google.com: icmp_seq=2 ttl=119 time=14.0 ms
64 bytes from google.com: icmp_seq=3 ttl=119 time=16.0 ms
        """
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (ping_output, '')
        mock_popen.return_value = mock_process

        with patch('shared.latency_utils.platform.system', return_value='Linux'):
            stats = ping_statistics('google.com', count=3)

        self.assertEqual(stats.status, LatencyStatus.SUCCESS)
        self.assertEqual(stats.packets_received, 3)
        self.assertEqual(stats.packet_loss_percent, 0)
        self.assertAlmostEqual(stats.avg_ms, 15.0, places=1)
        self.assertEqual(stats.min_ms, 14.0)
        self.assertEqual(stats.max_ms, 16.0)
        self.assertGreater(stats.stddev_ms, 0)  # Jitter should be > 0

    @patch('shared.latency_utils.subprocess.Popen')
    def test_ping_statistics_no_response(self, mock_popen):
        """Test ping with no response."""
        ping_output = """
PING invalid.local (127.0.0.1) 56(84) bytes of data.

--- invalid.local statistics ---
10 packets transmitted, 0 received, 100% packet loss, time 9127ms
        """
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (ping_output, '')
        mock_popen.return_value = mock_process

        with patch('shared.latency_utils.platform.system', return_value='Linux'):
            stats = ping_statistics('invalid.local', count=10)

        self.assertEqual(stats.status, LatencyStatus.UNREACHABLE)
        self.assertEqual(stats.packet_loss_percent, 100)

    @patch('shared.latency_utils.subprocess.Popen')
    def test_ping_statistics_timeout(self, mock_popen):
        """Test ping command timeout."""
        mock_popen.side_effect = Exception("Command timeout")

        with patch('shared.latency_utils.platform.system', return_value='Linux'):
            stats = ping_statistics('8.8.8.8', count=5, timeout=1)

        self.assertEqual(stats.status, LatencyStatus.ERROR)
        self.assertIsNotNone(stats.error_message)

    @patch('shared.latency_utils._has_mtr', return_value=False)
    @patch('shared.latency_utils.subprocess.Popen')
    def test_mtr_style_trace_fallback(self, mock_popen, mock_has_mtr):
        """Test MTR fallback to traceroute when mtr unavailable."""
        traceroute_output = """
traceroute to 8.8.8.8 (8.8.8.8), 30 hops max
 1  gateway.local (192.168.1.1)  2.123 ms  2.234 ms  2.345 ms
 2  isp.local (10.0.0.1)  15.123 ms  14.234 ms  16.234 ms
 3  8.8.8.8 (8.8.8.8)  35.123 ms  34.234 ms  36.234 ms
        """
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (traceroute_output, '')
        mock_popen.return_value = mock_process

        with patch('shared.latency_utils.platform.system', return_value='Linux'):
            hops, message = mtr_style_trace('8.8.8.8')

        self.assertGreater(len(hops), 0)
        self.assertIn('completed', message.lower())


class TestPhase3Integration(unittest.TestCase):
    """Integration tests for Phase 3 modules."""

    def test_dns_result_to_dict(self):
        """Test DNS result dictionary conversion."""
        from shared.dns_utils import DNSRecord

        result = DNSLookupResult(
            hostname='test.com',
            ipv4_addresses=['1.2.3.4'],
            ipv6_addresses=[],
            reverse_dns=None,
            lookup_time_ms=25.5,
            status=DNSStatus.SUCCESS
        )
        result.records = [
            DNSRecord('A', '1.2.3.4', 25.5, DNSStatus.SUCCESS)
        ]

        result_dict = result.to_dict()

        self.assertEqual(result_dict['hostname'], 'test.com')
        self.assertEqual(result_dict['ipv4_addresses'], ['1.2.3.4'])
        self.assertEqual(result_dict['status'], 'success')
        self.assertEqual(len(result_dict['records']), 1)

    def test_port_result_to_dict(self):
        """Test port check result dictionary conversion."""
        from shared.port_utils import PortCheckResult

        result = PortCheckResult(
            host='localhost',
            port=22,
            status=PortStatus.OPEN,
            service_name='SSH',
            response_time_ms=10.5
        )

        result_dict = result.to_dict()

        self.assertEqual(result_dict['port'], 22)
        self.assertEqual(result_dict['status'], 'open')
        self.assertEqual(result_dict['service_name'], 'SSH')

    def test_ping_statistics_result_to_dict(self):
        """Test ping statistics result dictionary conversion."""
        stats = PingStatistics(
            host='8.8.8.8',
            packets_sent=5,
            packets_received=5,
            packet_loss_percent=0,
            min_ms=10.0,
            avg_ms=15.0,
            max_ms=20.0,
            stddev_ms=3.5,
            status=LatencyStatus.SUCCESS,
            rtt_values=[10.0, 14.0, 15.0, 16.0, 20.0]
        )

        stats_dict = stats.to_dict()

        self.assertEqual(stats_dict['host'], '8.8.8.8')
        self.assertEqual(stats_dict['status'], 'success')
        self.assertEqual(stats_dict['packet_loss_percent'], 0)
        self.assertLessEqual(len(stats_dict['rtt_values']), 5)


if __name__ == '__main__':
    unittest.main()
