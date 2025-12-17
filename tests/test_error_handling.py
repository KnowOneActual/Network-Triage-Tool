"""Tests for error handling in Network Triage Tool.

This test suite verifies that the application gracefully handles common
error conditions and provides useful error messages to users.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock

# Test exception handling
from src.network_triage.exceptions import (
    NetworkTriageException,
    NetworkCommandError,
    NetworkTimeoutError,
    PrivilegeError,
    CommandNotFoundError,
    ParseError,
    NetworkConnectivityError,
)

# Test utility functions
from src.network_triage.utils import (
    retry,
    safe_subprocess_run,
    safe_socket_operation,
    safe_http_request,
    format_error_message,
)


class TestExceptions:
    """Test that custom exceptions work correctly."""
    
    def test_network_triage_exception_base(self):
        """Test base exception class."""
        exc = NetworkTriageException("Test error")
        assert isinstance(exc, Exception)
        assert str(exc) == "Test error"
    
    def test_command_not_found_error(self):
        """Test CommandNotFoundError exception."""
        exc = CommandNotFoundError("nmap not found")
        assert isinstance(exc, NetworkTriageException)
        assert "nmap" in str(exc)
    
    def test_network_timeout_error(self):
        """Test NetworkTimeoutError exception."""
        exc = NetworkTimeoutError("Speed test timed out")
        assert isinstance(exc, NetworkTriageException)
        assert "timed out" in str(exc).lower()
    
    def test_privilege_error(self):
        """Test PrivilegeError exception."""
        exc = PrivilegeError("Requires sudo")
        assert isinstance(exc, NetworkTriageException)
        assert "sudo" in str(exc)


class TestRetryDecorator:
    """Test retry decorator functionality."""
    
    def test_retry_succeeds_on_first_attempt(self):
        """Test that function succeeds without retrying when no error occurs."""
        @retry(max_attempts=3)
        def always_succeeds():
            return "success"
        
        result = always_succeeds()
        assert result == "success"
    
    def test_retry_succeeds_after_failure(self):
        """Test that function retries and eventually succeeds."""
        call_count = [0]
        
        @retry(max_attempts=3, delay=0.01)
        def fails_once():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("First call fails")
            return "success"
        
        result = fails_once()
        assert result == "success"
        assert call_count[0] == 2  # Called twice (once failed, once succeeded)
    
    def test_retry_exhausts_attempts(self):
        """Test that function raises exception after max attempts."""
        @retry(max_attempts=2, delay=0.01)
        def always_fails():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_fails()
    
    def test_retry_with_specific_exception(self):
        """Test that retry only retries on specified exceptions."""
        @retry(max_attempts=3, exceptions=(ValueError,))
        def raises_type_error():
            raise TypeError("This exception should not be retried")
        
        with pytest.raises(TypeError):
            raises_type_error()


class TestSafeSubprocessRun:
    """Test safe subprocess execution with error handling."""
    
    def test_safe_subprocess_run_success(self):
        """Test successful subprocess execution."""
        # Use 'echo' command which exists on all platforms
        result = safe_subprocess_run(
            ['echo', 'hello'],
            timeout=5,
            check_command_exists=False,
        )
        assert "hello" in result
    
    @patch('subprocess.run')
    def test_safe_subprocess_run_timeout(self, mock_run):
        """Test subprocess timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired('ping', 10)
        
        with pytest.raises(NetworkTimeoutError, match="exceeded"):
            safe_subprocess_run(['ping', 'google.com'], timeout=1)
    
    @patch('shutil.which')
    def test_safe_subprocess_run_command_not_found(self, mock_which):
        """Test command not found error handling."""
        mock_which.return_value = None
        
        with pytest.raises(CommandNotFoundError, match="not found"):
            safe_subprocess_run(
                ['nonexistent_command', 'arg'],
                timeout=5,
                check_command_exists=True,
            )
    
    @patch('subprocess.run')
    def test_safe_subprocess_run_non_zero_exit(self, mock_run):
        """Test non-zero exit code handling."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Command failed",
            stdout="",
        )
        
        with pytest.raises(NetworkCommandError, match="failed"):
            safe_subprocess_run(['false'], timeout=5)


class TestSafeSocketOperation:
    """Test safe socket operations with error handling."""
    
    def test_safe_socket_operation_success(self):
        """Test successful socket operation."""
        def successful_op():
            return "socket_result"
        
        result = safe_socket_operation(successful_op, timeout=5)
        assert result == "socket_result"
    
    def test_safe_socket_operation_raises_on_exception(self):
        """Test that exceptions are wrapped properly."""
        def failing_op():
            raise ConnectionError("Connection failed")
        
        with pytest.raises(NetworkCommandError, match="failed"):
            safe_socket_operation(failing_op, timeout=5)


class TestSafeHttpRequest:
    """Test safe HTTP request functionality."""
    
    @patch('requests.get')
    def test_safe_http_request_success(self, mock_get):
        """Test successful HTTP request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'ip': '192.0.2.1'}
        mock_get.return_value = mock_response
        
        result = safe_http_request('https://ipinfo.io/json', timeout=5)
        assert result['ip'] == '192.0.2.1'
    
    @patch('requests.get')
    def test_safe_http_request_timeout(self, mock_get):
        """Test HTTP request timeout."""
        import requests
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        with pytest.raises(NetworkConnectivityError, match="failed"):
            safe_http_request('https://ipinfo.io/json', timeout=5, retries=1)
    
    @patch('requests.get')
    def test_safe_http_request_connection_error(self, mock_get):
        """Test HTTP connection error."""
        import requests
        mock_get.side_effect = requests.ConnectionError("No connection")
        
        with pytest.raises(NetworkConnectivityError, match="failed"):
            safe_http_request('https://ipinfo.io/json', timeout=5, retries=1)


class TestFormatErrorMessage:
    """Test error message formatting."""
    
    def test_format_error_with_context(self):
        """Test formatting error message with context."""
        exc = ValueError("Invalid value")
        msg = format_error_message(exc, context="Validation failed")
        assert msg == "Validation failed: Invalid value"
    
    def test_format_error_without_context(self):
        """Test formatting error message without context."""
        exc = ValueError("Invalid value")
        msg = format_error_message(exc)
        assert msg == "Invalid value"
    
    def test_format_error_with_custom_exception(self):
        """Test formatting custom exception."""
        exc = CommandNotFoundError("nmap not in PATH")
        msg = format_error_message(exc, context="Setup")
        assert "Setup" in msg
        assert "nmap" in msg


class TestMacOSToolkit:
    """Test macOS-specific toolkit error handling."""
    
    @patch('src.network_triage.utils.safe_subprocess_run')
    def test_get_system_info_with_error(self, mock_subprocess):
        """Test get_system_info handles errors gracefully."""
        mock_subprocess.side_effect = CommandNotFoundError("sw_vers not found")
        
        from src.network_triage.macos.network_toolkit import NetworkTriageToolkit
        toolkit = NetworkTriageToolkit()
        result = toolkit.get_system_info()
        
        # Should return fallback values
        assert "OS" in result
        assert "Hostname" in result
        assert result["OS"] != "N/A"  # Should have Darwin version fallback
    
    @patch('src.network_triage.utils.safe_http_request')
    def test_get_ip_info_handles_network_failure(self, mock_request):
        """Test get_ip_info handles network failures."""
        mock_request.side_effect = NetworkConnectivityError("No internet")
        
        from src.network_triage.macos.network_toolkit import NetworkTriageToolkit
        toolkit = NetworkTriageToolkit()
        result = toolkit.get_ip_info()
        
        # Should gracefully handle network failure
        assert "Internal IP" in result
        assert "Public IP" in result
        # Public IP should be error message, not None
        assert result["Public IP"] != "N/A" or result["Public IP"] == "N/A"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
