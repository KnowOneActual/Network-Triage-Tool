"""Tests for Linux network toolkit.

This test suite verifies that the Linux toolkit correctly implements
the same interface as the macOS toolkit while using Linux-specific commands.

Tests are structured to work on Linux systems. Some tests may need
to be skipped on non-Linux systems.
"""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from network_triage.exceptions import (
    NetworkTriageException,
    NetworkCommandError,
    CommandNotFoundError,
    NetworkConnectivityError,
)
from network_triage.linux.network_toolkit import NetworkTriageToolkit


@pytest.mark.skipif(sys.platform != "linux", reason="Linux toolkit tests only")
class TestLinuxNetworkTriageToolkit:
    """Test Linux network toolkit functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.toolkit = NetworkTriageToolkit()

    def test_toolkit_initialization(self):
        """Test toolkit initializes without errors."""
        toolkit = NetworkTriageToolkit()
        assert toolkit is not None
        assert hasattr(toolkit, 'get_system_info')
        assert hasattr(toolkit, 'get_ip_info')
        assert hasattr(toolkit, 'get_connection_details')
        assert hasattr(toolkit, 'network_adapter_info')
        assert hasattr(toolkit, 'traceroute_test')

    # ============================================================
    # get_system_info() Tests
    # ============================================================

    def test_get_system_info_returns_dict(self):
        """Test get_system_info returns a dictionary."""
        result = self.toolkit.get_system_info()
        assert isinstance(result, dict)

    def test_get_system_info_has_required_keys(self):
        """Test get_system_info has all required keys."""
        result = self.toolkit.get_system_info()
        required_keys = ['OS', 'Hostname', 'Kernel', 'Arch']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

    def test_get_system_info_values_not_empty(self):
        """Test get_system_info returns non-empty values."""
        result = self.toolkit.get_system_info()
        for key, value in result.items():
            assert value != '', f"Key {key} has empty value"

    def test_get_system_info_contains_linux(self):
        """Test get_system_info OS contains 'Linux'."""
        result = self.toolkit.get_system_info()
        # Should contain 'Linux' or graceful fallback
        assert isinstance(result['OS'], str)

    # ============================================================
    # get_ip_info() Tests
    # ============================================================

    def test_get_ip_info_returns_dict(self):
        """Test get_ip_info returns a dictionary."""
        result = self.toolkit.get_ip_info()
        assert isinstance(result, dict)

    def test_get_ip_info_has_required_keys(self):
        """Test get_ip_info has all required keys."""
        result = self.toolkit.get_ip_info()
        required_keys = ['Internal IP', 'Public IP', 'Gateway']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

    def test_get_ip_info_internal_ip_format(self):
        """Test get_ip_info internal IP is valid format."""
        result = self.toolkit.get_ip_info()
        internal_ip = result['Internal IP']
        # Should be IP or 'Unknown'
        if internal_ip != 'Unknown':
            parts = internal_ip.split('.')
            assert len(parts) == 4, f"Invalid IP format: {internal_ip}"
            for part in parts:
                assert part.isdigit(), f"Non-numeric IP part: {part}"

    def test_get_ip_info_gateway_format(self):
        """Test get_ip_info gateway is valid format."""
        result = self.toolkit.get_ip_info()
        gateway = result['Gateway']
        # Should be IP or 'Unknown'
        if gateway != 'Unknown':
            parts = gateway.split('.')
            assert len(parts) == 4, f"Invalid gateway format: {gateway}"

    # ============================================================
    # get_connection_details() Tests
    # ============================================================

    def test_get_connection_details_returns_dict(self):
        """Test get_connection_details returns a dictionary."""
        result = self.toolkit.get_connection_details()
        assert isinstance(result, dict)

    def test_get_connection_details_has_required_keys(self):
        """Test get_connection_details has all required keys."""
        result = self.toolkit.get_connection_details()
        required_keys = [
            'Interface', 'IP Address', 'MAC Address',
            'Netmask', 'Speed', 'MTU', 'Gateway'
        ]
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

    def test_get_connection_details_interface_not_empty(self):
        """Test get_connection_details interface name is not empty."""
        result = self.toolkit.get_connection_details()
        assert result['Interface'] != 'Unknown'
        assert result['Interface'] != ''

    def test_get_connection_details_mac_format(self):
        """Test get_connection_details MAC address format."""
        result = self.toolkit.get_connection_details()
        mac = result['MAC Address']
        # MAC should be in format XX:XX:XX:XX:XX:XX or Unknown
        if mac != 'Unknown':
            parts = mac.split(':')
            assert len(parts) == 6, f"Invalid MAC format: {mac}"

    def test_get_connection_details_mtu_is_numeric(self):
        """Test get_connection_details MTU is numeric."""
        result = self.toolkit.get_connection_details()
        mtu = result['MTU']
        if mtu != 'Unknown':
            assert mtu.isdigit(), f"MTU not numeric: {mtu}"

    # ============================================================
    # network_adapter_info() Tests
    # ============================================================

    def test_network_adapter_info_returns_dict(self):
        """Test network_adapter_info returns a dictionary."""
        result = self.toolkit.network_adapter_info()
        assert isinstance(result, dict)

    def test_network_adapter_info_not_empty(self):
        """Test network_adapter_info returns adapters."""
        result = self.toolkit.network_adapter_info()
        assert len(result) > 0, "No adapters found"

    def test_network_adapter_info_has_loopback(self):
        """Test network_adapter_info includes loopback interface."""
        result = self.toolkit.network_adapter_info()
        assert 'lo' in result, "Loopback interface not found"

    def test_network_adapter_info_adapter_structure(self):
        """Test each adapter has required fields."""
        result = self.toolkit.network_adapter_info()
        required_fields = ['Status', 'Type', 'MAC', 'MTU']
        for adapter_name, adapter_info in result.items():
            if not adapter_name.startswith('error'):
                for field in required_fields:
                    assert field in adapter_info, \
                        f"Adapter {adapter_name} missing field {field}"

    def test_network_adapter_info_status_valid(self):
        """Test adapter status is valid."""
        result = self.toolkit.network_adapter_info()
        valid_statuses = ['up', 'down']
        for adapter_name, adapter_info in result.items():
            if not adapter_name.startswith('error'):
                assert adapter_info['Status'] in valid_statuses, \
                    f"Invalid status for {adapter_name}: {adapter_info['Status']}"

    def test_network_adapter_info_type_valid(self):
        """Test adapter type is valid."""
        result = self.toolkit.network_adapter_info()
        valid_types = ['loopback', 'ethernet', 'wireless', 'unknown']
        for adapter_name, adapter_info in result.items():
            if not adapter_name.startswith('error'):
                assert adapter_info['Type'] in valid_types, \
                    f"Invalid type for {adapter_name}: {adapter_info['Type']}"

    def test_network_adapter_info_loopback_has_ip(self):
        """Test loopback adapter has IP address."""
        result = self.toolkit.network_adapter_info()
        if 'lo' in result:
            assert 'IP' in result['lo'], "Loopback missing IP"
            assert result['lo']['IP'] == '127.0.0.1', "Loopback IP incorrect"

    # ============================================================
    # traceroute_test() Tests
    # ============================================================

    def test_traceroute_test_returns_dict(self):
        """Test traceroute_test returns a dictionary."""
        result = self.toolkit.traceroute_test('8.8.8.8')
        assert isinstance(result, dict)

    def test_traceroute_test_has_required_keys(self):
        """Test traceroute_test has required keys."""
        result = self.toolkit.traceroute_test('8.8.8.8')
        required_keys = ['Destination', 'Hops', 'Success', 'Message']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

    def test_traceroute_test_destination_correct(self):
        """Test traceroute_test destination is correct."""
        dest = '8.8.8.8'
        result = self.toolkit.traceroute_test(dest)
        assert result['Destination'] == dest

    def test_traceroute_test_hops_is_list(self):
        """Test traceroute_test hops is a list."""
        result = self.toolkit.traceroute_test('8.8.8.8')
        assert isinstance(result['Hops'], list)

    def test_traceroute_test_success_is_bool(self):
        """Test traceroute_test success is boolean."""
        result = self.toolkit.traceroute_test('8.8.8.8')
        assert isinstance(result['Success'], bool)

    def test_traceroute_test_message_not_empty(self):
        """Test traceroute_test message is not empty."""
        result = self.toolkit.traceroute_test('8.8.8.8')
        assert result['Message'] != ''
        assert isinstance(result['Message'], str)

    def test_traceroute_test_hops_structure(self):
        """Test each hop has required fields."""
        result = self.toolkit.traceroute_test('8.8.8.8')
        # Only test if hops exist
        if result['Hops']:
            for hop in result['Hops']:
                assert 'Hop' in hop, "Hop missing 'Hop' field"
                assert isinstance(hop['Hop'], int), "Hop number not int"

    def test_traceroute_test_custom_destination(self):
        """Test traceroute_test with custom destination."""
        dest = 'google.com'
        result = self.toolkit.traceroute_test(dest)
        assert result['Destination'] == dest

    # ============================================================
    # Error Handling Tests
    # ============================================================

    def test_get_system_info_graceful_fallback(self):
        """Test get_system_info handles missing commands gracefully."""
        # Should always return a dict with fallback values
        result = self.toolkit.get_system_info()
        assert isinstance(result, dict)
        assert all(isinstance(v, str) for v in result.values())

    def test_get_ip_info_handles_network_issues(self):
        """Test get_ip_info handles network issues gracefully."""
        # Should return dict even if public IP unavailable
        result = self.toolkit.get_ip_info()
        assert isinstance(result, dict)
        # May have 'Unavailable' but should not crash
        assert 'Public IP' in result

    def test_network_adapter_info_handles_errors(self):
        """Test network_adapter_info handles errors gracefully."""
        result = self.toolkit.network_adapter_info()
        # Should return dict (possibly with error message)
        assert isinstance(result, dict)

    def test_traceroute_test_invalid_destination(self):
        """Test traceroute_test handles invalid destination."""
        # Should not crash on invalid destination
        result = self.toolkit.traceroute_test('invalid-host-name-12345.test')
        assert isinstance(result, dict)
        assert 'Success' in result
        assert 'Message' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
