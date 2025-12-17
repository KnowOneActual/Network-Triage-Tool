"""Custom exception classes for Network Triage Tool.

These exceptions provide specific error types for different failure modes,
making it easier to debug and handle errors gracefully.
"""


class NetworkTriageException(Exception):
    """Base exception for all Network Triage Tool errors."""
    pass


class NetworkCommandError(NetworkTriageException):
    """Raised when a system network command fails to execute.
    
    Examples:
        - ping command not found
        - ifconfig fails
        - system_profiler returns error
    """
    pass


class NetworkTimeoutError(NetworkTriageException):
    """Raised when a network operation times out.
    
    Examples:
        - Speed test takes too long
        - DNS lookup timeout
        - Connection attempt timeout
    """
    pass


class PrivilegeError(NetworkTriageException):
    """Raised when an operation requires elevated privileges.
    
    Examples:
        - Packet capture requires root
        - Nmap service detection requires sudo
    """
    pass


class CommandNotFoundError(NetworkTriageException):
    """Raised when a required command is not installed or in PATH.
    
    Examples:
        - nmap not installed
        - traceroute not found
    """
    pass


class ParseError(NetworkTriageException):
    """Raised when parsing output from a command fails.
    
    Examples:
        - XML parsing fails
        - Regex pattern doesn't match
    """
    pass


class NetworkConnectivityError(NetworkTriageException):
    """Raised when basic network connectivity is unavailable.
    
    Examples:
        - Cannot reach public IP address
        - DNS server unreachable
        - Gateway unreachable
    """
    pass
