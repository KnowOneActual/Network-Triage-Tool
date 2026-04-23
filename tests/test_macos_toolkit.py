"""Tests for macOS-specific network toolkit.

Verifies data gathering from macOS-native tools like system_profiler,
scutil, and sw_vers using comprehensive mocking.
"""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from network_triage.exceptions import CommandNotFoundError
from network_triage.macos.network_toolkit import NetworkTriageToolkit

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture
def toolkit() -> NetworkTriageToolkit:
    """Toolkit instance for testing."""
    return NetworkTriageToolkit()


@pytest.fixture
def mock_psutil(mocker: MockerFixture) -> dict[str, Any]:
    """Mock psutil network functions."""
    mock_addrs = mocker.patch("psutil.net_if_addrs")
    mock_stats = mocker.patch("psutil.net_if_stats")
    return {"addrs": mock_addrs, "stats": mock_stats}


class TestMacOSGetSystemInfo:
    """Test get_system_info method."""

    def test_get_system_info_success(self, toolkit: NetworkTriageToolkit, mocker: MockerFixture) -> None:
        """Test successful system info retrieval with marketing name."""
        mocker.patch("platform.system", return_value="Darwin")
        mocker.patch("platform.release", return_value="23.1.0")
        mocker.patch("socket.gethostname", return_value="Test-Mac.local")

        mock_run = mocker.patch("network_triage.macos.network_toolkit.safe_subprocess_run")
        # sw_vers -productName, then sw_vers -productVersion
        mock_run.side_effect = ["macOS", "14.1.2"]

        result = toolkit.get_system_info()

        assert result["Hostname"] == "Test-Mac.local"
        assert "macOS Sonoma" in result["OS"]
        assert "Darwin 23.1.0" in result["OS"]

    def test_get_system_info_fallback(self, toolkit: NetworkTriageToolkit, mocker: MockerFixture) -> None:
        """Test system info retrieval when sw_vers fails."""
        mocker.patch("platform.system", return_value="Darwin")
        mocker.patch("platform.release", return_value="23.1.0")

        mock_run = mocker.patch("network_triage.macos.network_toolkit.safe_subprocess_run")
        mock_run.side_effect = CommandNotFoundError("sw_vers not found")

        result = toolkit.get_system_info()

        assert "macOS (Darwin 23.1.0)" in result["OS"]


class TestMacOSGetIpInfo:
    """Test get_ip_info method."""

    def test_get_ip_info_success(self, toolkit: NetworkTriageToolkit, mocker: MockerFixture) -> None:
        """Test successful retrieval of all IP info."""
        # Mock internal IP socket
        mock_socket_class = mocker.patch("socket.socket")
        mock_sock_instance = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_sock_instance
        mock_sock_instance.getsockname.return_value = ("192.168.1.50", 12345)

        # Mock gateway netstat
        netstat_output = "default            192.168.1.1        UGSc           en0"
        mocker.patch("network_triage.macos.network_toolkit.safe_subprocess_run", return_value=netstat_output)

        # Mock public IP
        mocker.patch("network_triage.macos.network_toolkit.safe_http_request", return_value={"ip": "1.2.3.4"})

        result = toolkit.get_ip_info()

        assert result["Internal IP"] == "192.168.1.50"
        assert result["Gateway"] == "192.168.1.1"
        assert result["Public IP"] == "1.2.3.4"


class TestMacOSGetConnectionDetails:
    """Test get_connection_details method."""

    def test_get_connection_details_wifi_success(
        self, toolkit: NetworkTriageToolkit, mocker: MockerFixture, mock_psutil: dict[str, Any]
    ) -> None:
        """Test detailed Wi-Fi connection info."""
        # 1. Mock netstat for interface
        netstat_output = "default            192.168.1.1        UGSc           en0"

        # 2. Mock system_profiler for Wi-Fi
        profiler_output = """
        en0:
          Card Type: Wi-Fi
          Current Network Information:
            MySSID:
              Channel: 36
              Signal / Noise: -50 dBm / -92 dBm
        """

        # 3. Mock scutil for DNS
        scutil_output = "nameserver[0] : 8.8.8.8\nnameserver[1] : 8.8.4.4"

        mock_run = mocker.patch("network_triage.macos.network_toolkit.safe_subprocess_run")
        mock_run.side_effect = [netstat_output, profiler_output, scutil_output]

        # 4. Mock psutil
        mock_psutil["addrs"].return_value = {
            "en0": [
                MagicMock(family=socket.AF_INET, address="192.168.1.50", netmask="255.255.255.0"),
                MagicMock(family=getattr(socket, "AF_LINK", 18), address="00:11:22:33:44:55"),
            ]
        }
        mock_psutil["stats"].return_value = {"en0": MagicMock(isup=True, speed=1000, mtu=1500)}

        result = toolkit.get_connection_details()

        assert result["Interface"] == "en0"
        assert result["Connection Type"] == "Wi-Fi"
        assert result["SSID"] == "MySSID"
        assert result["Channel"] == "36"
        assert result["Signal"] == "-50 dBm"
        assert result["Noise"] == "-92 dBm"
        assert result["DNS Servers"] == "8.8.4.4, 8.8.8.8"
        assert result["IP Address"] == "192.168.1.50"
        assert result["MAC Address"] == "00:11:22:33:44:55"
        assert result["Status"] == "Up"


class TestMacOSTraceroute:
    """Test traceroute_test method."""

    def test_traceroute_requires_sudo(self, toolkit: NetworkTriageToolkit, mocker: MockerFixture) -> None:
        """Test that traceroute reports sudo requirement."""
        mocker.patch("os.geteuid", return_value=501)  # Non-root

        result = toolkit.traceroute_test("8.8.8.8")
        assert "administrator privileges" in result

    def test_traceroute_success_as_root(self, toolkit: NetworkTriageToolkit, mocker: MockerFixture) -> None:
        """Test successful traceroute when running as root."""
        mocker.patch("os.geteuid", return_value=0)  # Root
        mocker.patch("network_triage.macos.network_toolkit.safe_subprocess_run", return_value="1  * * *\n2  8.8.8.8  10ms")

        result = toolkit.traceroute_test("8.8.8.8")
        assert "Traceroute to 8.8.8.8" in result
        assert "8.8.8.8" in result
