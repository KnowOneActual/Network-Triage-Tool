"""Unit tests for Phase 3 Advanced Diagnostics modules.

Tests DNS utilities, port connectivity, and latency measurement functions.
Uses modern pytest patterns, fixtures, and mocker.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from shared.dns_utils import (
    DNSLookupResult,
    DNSStatus,
    check_dns_propagation,
    resolve_hostname,
    validate_dns_server,
)
from shared.latency_utils import (
    LatencyStatus,
    PingStatistics,
    _parse_ping_output,
    mtr_style_trace,
    ping_statistics,
)
from shared.port_utils import (
    PortStatus,
    check_multiple_ports,
    check_port_open,
    get_service_name,
    summarize_port_scan,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture
def mock_dns_socket(mocker: MockerFixture) -> Any:
    """Specific socket mock for DNS utils."""
    return mocker.patch("shared.dns_utils.socket")


@pytest.fixture
def mock_port_socket(mocker: MockerFixture) -> Any:
    """Specific socket mock for Port utils."""
    return mocker.patch("shared.port_utils.socket")


class TestDNSUtils:
    """Test suite for DNS utilities module."""

    def test_resolve_hostname_success(self, mock_dns_socket: Any) -> None:
        """Test successful hostname resolution."""
        mock_dns_socket.getaddrinfo.return_value = [
            (2, 1, 6, "", ("142.250.185.46", 0)),  # IPv4
            (10, 1, 6, "", ("2607:f8b0:4004:809::200e", 0)),  # IPv6
        ]
        mock_dns_socket.AF_INET = 2
        mock_dns_socket.AF_INET6 = 10
        mock_dns_socket.SOCK_STREAM = 1
        mock_dns_socket.AF_UNSPEC = 0

        result = resolve_hostname("google.com")

        assert result.hostname == "google.com"
        assert len(result.ipv4_addresses) == 1
        assert len(result.ipv6_addresses) == 1
        assert result.status == DNSStatus.SUCCESS

    def test_resolve_hostname_not_found(self, mock_dns_socket: Any) -> None:
        """Test hostname not found scenario."""
        import socket

        mock_dns_socket.gaierror = socket.gaierror
        mock_dns_socket.getaddrinfo.side_effect = socket.gaierror("Name or service not known")
        mock_dns_socket.AF_UNSPEC = 0
        mock_dns_socket.SOCK_STREAM = 1

        result = resolve_hostname("invalid-hostname-12345.com")

        assert result.status == DNSStatus.NOT_FOUND
        assert len(result.ipv4_addresses) == 0
        assert result.error_message is not None

    def test_resolve_hostname_timeout(self, mock_dns_socket: Any) -> None:
        """Test DNS resolution timeout."""
        import socket

        mock_dns_socket.timeout = socket.timeout
        mock_dns_socket.getaddrinfo.side_effect = TimeoutError("DNS query timed out")
        mock_dns_socket.AF_UNSPEC = 0
        mock_dns_socket.SOCK_STREAM = 1

        result = resolve_hostname("slow-dns.example.com", timeout=1)

        assert result.status in [DNSStatus.TIMEOUT, DNSStatus.NOT_FOUND, DNSStatus.ERROR]

    def test_validate_dns_server_responsive(self, mock_dns_socket: Any) -> None:
        """Test DNS server validation - responsive server."""
        mock_sock_instance = MagicMock()
        mock_dns_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.recvfrom.return_value = (b"\x00\x01\x81\x80" + b"\x00" * 8, ("8.8.8.8", 53))

        result = validate_dns_server("8.8.8.8")

        assert result["is_responsive"] is True
        assert result["status"] == "responsive"
        assert result["server_ip"] == "8.8.8.8"

    def test_validate_dns_server_timeout(self, mock_dns_socket: Any) -> None:
        """Test DNS server validation - timeout."""
        mock_sock_instance = MagicMock()
        mock_dns_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.recvfrom.side_effect = Exception("Socket timeout")

        result = validate_dns_server("invalid-server.local", timeout=1)

        assert result["is_responsive"] is False
        assert result["status"] in ["timeout", "error", "no_response"]

    @pytest.mark.asyncio
    async def test_check_dns_propagation(self, mocker: MockerFixture) -> None:
        """Test DNS propagation check across providers."""
        mock_gethostbyname = mocker.patch("shared.dns_utils.socket.gethostbyname_ex")
        mock_gethostbyname.return_value = ("google.com", [], ["142.250.185.46"])

        results = await check_dns_propagation("google.com")

        assert len(results) > 0
        for result in results:
            assert "provider" in result
            assert "status" in result
            assert "ips" in result


class TestPortUtils:
    """Test suite for port utilities module."""

    def test_check_port_open(self, mock_port_socket: Any) -> None:
        """Test port check - port is open."""
        mock_sock_instance = MagicMock()
        mock_port_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None

        result = check_port_open("localhost", 22)

        assert result.status == PortStatus.OPEN
        assert result.port == 22
        assert result.service_name == "SSH"
        assert result.response_time_ms >= 0

    def test_check_port_closed(self, mocker: MockerFixture) -> None:
        """Test port check - port is closed."""
        mock_sock_class = mocker.patch("shared.port_utils.socket.socket")
        mock_sock_instance = MagicMock()
        mock_sock_class.return_value = mock_sock_instance
        mock_sock_instance.connect.side_effect = ConnectionRefusedError()

        result = check_port_open("localhost", 54321)

        assert result.status == PortStatus.CLOSED

    def test_check_port_timeout(self, mocker: MockerFixture) -> None:
        """Test port check - timeout (filtered port)."""
        mock_sock_class = mocker.patch("shared.port_utils.socket.socket")
        mock_sock_instance = MagicMock()
        mock_sock_class.return_value = mock_sock_instance
        mock_sock_instance.connect.side_effect = TimeoutError("Connection timeout")

        result = check_port_open("10.255.255.1", 22, timeout=1)

        assert result.status == PortStatus.FILTERED

    def test_check_port_invalid_port(self) -> None:
        """Test port check - invalid port number."""
        result = check_port_open("localhost", 99999)

        assert result.status == PortStatus.ERROR
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_check_multiple_ports(self, mocker: MockerFixture) -> None:
        """Test concurrent port checking."""
        mock_check_port = mocker.patch("shared.port_utils.check_port_open")
        results = [
            MagicMock(port=22, status=PortStatus.OPEN, service_name="SSH"),
            MagicMock(port=80, status=PortStatus.CLOSED, service_name="HTTP"),
        ]
        mock_check_port.side_effect = results

        result = await check_multiple_ports("localhost", [22, 80])

        assert len(result) == 2

    @pytest.mark.parametrize(
        ("port", "expected_name"),
        [
            (22, "SSH"),
            (80, "HTTP"),
            (443, "HTTPS"),
            (99999, "Unknown"),
        ],
    )
    def test_get_service_name(self, port: int, expected_name: str) -> None:
        """Test service name lookup."""
        assert get_service_name(port) == expected_name

    def test_summarize_port_scan(self) -> None:
        """Test port scan result summarization."""
        from shared.port_utils import PortCheckResult

        results = [
            PortCheckResult(
                host="localhost",
                port=22,
                status=PortStatus.OPEN,
                service_name="SSH",
                response_time_ms=15.5,
            ),
            PortCheckResult(
                host="localhost",
                port=23,
                status=PortStatus.CLOSED,
                service_name="TELNET",
                response_time_ms=2.1,
            ),
        ]
        summary = summarize_port_scan(results)

        assert summary["total_scanned"] == 2
        assert summary["open_count"] == 1
        assert summary["closed_count"] == 1
        assert summary["avg_response_time_ms"] > 0


class TestLatencyUtils:
    """Test suite for latency utilities module."""

    def test_parse_ping_output_linux(self, sample_ping_output_linux: str) -> None:
        """Test ping output parsing for Linux."""
        rtt_values = _parse_ping_output(sample_ping_output_linux, "Linux")

        assert len(rtt_values) == 3
        assert rtt_values[0] == pytest.approx(15.123, rel=1e-2)
        assert rtt_values[1] == pytest.approx(14.856, rel=1e-2)
        assert rtt_values[2] == pytest.approx(16.234, rel=1e-2)

    def test_parse_ping_output_windows(self, sample_ping_output_windows: str) -> None:
        """Test ping output parsing for Windows."""
        rtt_values = _parse_ping_output(sample_ping_output_windows, "Windows")

        assert len(rtt_values) == 3
        assert rtt_values == [20.0, 19.0, 21.0]

    def test_ping_statistics_success(self, mocker: MockerFixture, sample_ping_output_linux: str) -> None:
        """Test ping statistics calculation."""
        mock_popen = mocker.patch("shared.latency_utils.subprocess.Popen")
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = io.StringIO(sample_ping_output_linux)
        mock_process.stderr = io.StringIO("")
        mock_process.poll.return_value = 0
        mock_popen.return_value = mock_process

        mocker.patch("shared.latency_utils.platform.system", return_value="Linux")
        stats = ping_statistics("google.com", count=3)

        assert stats.status == LatencyStatus.SUCCESS
        assert stats.packets_received == 3
        assert stats.packet_loss_percent == 0
        assert stats.avg_ms == pytest.approx(15.0, rel=1e-1)
        assert stats.min_ms == 14.856
        assert stats.max_ms == 16.234
        assert stats.stddev_ms > 0

    def test_ping_statistics_no_response(self, mocker: MockerFixture) -> None:
        """Test ping with no response."""
        ping_output = """
PING invalid.local (127.0.0.1) 56(84) bytes of data.

--- invalid.local statistics ---
10 packets transmitted, 0 received, 100% packet loss, time 9127ms
        """
        mock_popen = mocker.patch("shared.latency_utils.subprocess.Popen")
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = io.StringIO(ping_output)
        mock_process.stderr = io.StringIO("")
        mock_process.poll.return_value = 0
        mock_popen.return_value = mock_process

        mocker.patch("shared.latency_utils.platform.system", return_value="Linux")
        stats = ping_statistics("invalid.local", count=10)

        assert stats.status == LatencyStatus.UNREACHABLE
        assert stats.packets_sent == 10
        assert stats.packets_received == 0
        assert stats.packet_loss_percent == 100

    def test_ping_statistics_timeout(self, mocker: MockerFixture) -> None:
        """Test ping command timeout."""
        mock_popen = mocker.patch("shared.latency_utils.subprocess.Popen")
        mock_popen.side_effect = Exception("Command timeout")

        mocker.patch("shared.latency_utils.platform.system", return_value="Linux")
        stats = ping_statistics("8.8.8.8", count=5, timeout=1)

        assert stats.status == LatencyStatus.ERROR
        assert stats.error_message is not None

    def test_mtr_style_trace_fallback(self, mocker: MockerFixture) -> None:
        """Test MTR fallback to traceroute when mtr unavailable."""
        traceroute_output = """
traceroute to 8.8.8.8 (8.8.8.8), 30 hops max
 1  gateway.local (192.168.1.1)  2.123 ms  2.234 ms  2.345 ms
 2  isp.local (10.0.0.1)  15.123 ms  14.234 ms  16.234 ms
 3  8.8.8.8 (8.8.8.8)  35.123 ms  34.234 ms  36.234 ms
        """
        mocker.patch("shared.latency_utils._has_mtr", return_value=False)
        mock_popen = mocker.patch("shared.latency_utils.subprocess.Popen")
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (traceroute_output, "")
        mock_popen.return_value = mock_process

        mocker.patch("shared.latency_utils.platform.system", return_value="Linux")
        hops, message = mtr_style_trace("8.8.8.8")

        assert len(hops) > 0
        assert "completed" in message.lower()


class TestPhase3Integration:
    """Integration tests for Phase 3 modules."""

    def test_dns_result_to_dict(self) -> None:
        """Test DNS result dictionary conversion."""
        from shared.dns_utils import DNSRecord

        result = DNSLookupResult(
            hostname="test.com",
            ipv4_addresses=["1.2.3.4"],
            ipv6_addresses=[],
            reverse_dns=None,
            lookup_time_ms=25.5,
            status=DNSStatus.SUCCESS,
        )
        result.records = [DNSRecord("A", "1.2.3.4", 25.5, DNSStatus.SUCCESS)]

        result_dict = result.to_dict()

        assert result_dict["hostname"] == "test.com"
        assert result_dict["ipv4_addresses"] == ["1.2.3.4"]
        assert result_dict["status"] == "success"
        assert len(result_dict["records"]) == 1

    def test_port_result_to_dict(self) -> None:
        """Test port check result dictionary conversion."""
        from shared.port_utils import PortCheckResult

        result = PortCheckResult(host="localhost", port=22, status=PortStatus.OPEN, service_name="SSH", response_time_ms=10.5)

        result_dict = result.to_dict()

        assert result_dict["port"] == 22
        assert result_dict["status"] == "open"
        assert result_dict["service_name"] == "SSH"

    def test_ping_statistics_result_to_dict(self) -> None:
        """Test ping statistics result dictionary conversion."""
        stats = PingStatistics(
            host="8.8.8.8",
            packets_sent=5,
            packets_received=5,
            packet_loss_percent=0,
            min_ms=10.0,
            avg_ms=15.0,
            max_ms=20.0,
            stddev_ms=3.5,
            status=LatencyStatus.SUCCESS,
            rtt_values=[10.0, 14.0, 15.0, 16.0, 20.0],
        )

        stats_dict = stats.to_dict()

        assert stats_dict["host"] == "8.8.8.8"
        assert stats_dict["status"] == "success"
        assert stats_dict["packet_loss_percent"] == 0
        assert len(stats_dict["rtt_values"]) <= 5
