# Error Handling Guide

Comprehensive guide to error handling patterns and best practices in the Network Triage Tool.

## Overview

The Network Triage Tool implements robust error handling across all modules to ensure reliability, provide clear user feedback, and enable graceful degradation when network operations fail. This guide documents the patterns, conventions, and best practices used throughout the codebase.

## Core Principles

### 1. **Never Crash the Application**
All network operations are wrapped in try-except blocks to prevent uncaught exceptions from terminating the application.

```python
# ✅ GOOD
try:
    result = socket.create_connection((host, port), timeout=5)
except socket.timeout:
    return PortCheckResult(status=PortStatus.TIMEOUT, error_message="Connection timed out")
except Exception as e:
    return PortCheckResult(status=PortStatus.ERROR, error_message=str(e))

# ❌ BAD - Can crash on network errors
result = socket.create_connection((host, port), timeout=5)
```

### 2. **Provide Actionable Error Messages**
Error messages should explain what went wrong and suggest how to fix it.

```python
# ✅ GOOD
if not hostname:
    return DNSLookupResult(
        status=DNSStatus.ERROR,
        error_message="Hostname cannot be empty. Please provide a valid domain name."
    )

# ❌ BAD - Unhelpful message
if not hostname:
    return DNSLookupResult(status=DNSStatus.ERROR, error_message="Invalid input")
```

### 3. **Use Status Enums for Categorization**
Classify errors using enums rather than relying on exception types or string matching.

```python
from enum import Enum

class PortStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    FILTERED = "filtered"
    TIMEOUT = "timeout"
    ERROR = "error"
```

### 4. **Timeout Protection on All Network Operations**
Every network operation must have a configurable timeout with sensible defaults.

```python
def resolve_hostname(hostname: str, timeout: int = 5) -> DNSLookupResult:
    socket.setdefaulttimeout(timeout)
    try:
        # Network operation here
        pass
    except socket.timeout:
        return DNSLookupResult(status=DNSStatus.TIMEOUT)
```

### 5. **Log Errors for Debugging**
Use Python's logging module to record errors for troubleshooting without exposing details to end users.

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    return error_result("Operation failed. Check logs for details.")
```

## Error Handling Patterns by Module

### DNS Utilities (`src/shared/dns_utils.py`)

#### Status Codes
```python
class DNSStatus(Enum):
    SUCCESS = "success"      # Resolution succeeded
    NOT_FOUND = "not_found"  # NXDOMAIN - domain doesn't exist
    TIMEOUT = "timeout"      # DNS query timed out
    ERROR = "error"          # Other errors (network, invalid input)
```

#### Pattern: Hostname Resolution

```python
def resolve_hostname(hostname: str, timeout: int = 5, include_reverse_dns: bool = True) -> DNSLookupResult:
    """
    Resolve hostname to IP addresses with comprehensive error handling.
    
    Args:
        hostname: Domain name to resolve
        timeout: Maximum time to wait (seconds)
        include_reverse_dns: Whether to perform reverse DNS lookup
    
    Returns:
        DNSLookupResult with status and addresses or error message
    """
    # Validate input
    if not hostname or not isinstance(hostname, str):
        return DNSLookupResult(
            host=hostname,
            status=DNSStatus.ERROR,
            error_message="Hostname must be a non-empty string"
        )
    
    # Set timeout for socket operations
    socket.setdefaulttimeout(timeout)
    start_time = time.time()
    
    try:
        # Attempt IPv4 resolution
        ipv4_addresses = []
        try:
            ipv4_info = socket.getaddrinfo(hostname, None, socket.AF_INET)
            ipv4_addresses = list(set(addr[4][0] for addr in ipv4_info))
        except socket.gaierror as e:
            if e.errno == socket.EAI_NONAME:
                # NXDOMAIN - legitimate "not found" result
                pass
            else:
                raise
        
        # Attempt IPv6 resolution
        ipv6_addresses = []
        try:
            ipv6_info = socket.getaddrinfo(hostname, None, socket.AF_INET6)
            ipv6_addresses = [normalize_ipv6(addr[4][0]) for addr in ipv6_info]
        except socket.gaierror:
            pass  # IPv6 not available
        
        # Check if we found anything
        if not ipv4_addresses and not ipv6_addresses:
            return DNSLookupResult(
                host=hostname,
                status=DNSStatus.NOT_FOUND,
                error_message=f"Domain '{hostname}' not found (NXDOMAIN)"
            )
        
        # Success - optionally get reverse DNS
        reverse_dns = None
        if include_reverse_dns and ipv4_addresses:
            try:
                reverse_dns = socket.gethostbyaddr(ipv4_addresses[0])[0]
            except (socket.herror, socket.gaierror):
                pass  # Reverse DNS optional
        
        lookup_time = (time.time() - start_time) * 1000
        
        return DNSLookupResult(
            host=hostname,
            ipv4_addresses=ipv4_addresses,
            ipv6_addresses=ipv6_addresses,
            reverse_dns=reverse_dns,
            status=DNSStatus.SUCCESS,
            lookup_time_ms=lookup_time
        )
    
    except socket.timeout:
        return DNSLookupResult(
            host=hostname,
            status=DNSStatus.TIMEOUT,
            error_message=f"DNS lookup timed out after {timeout} seconds. Try increasing timeout or check DNS server."
        )
    
    except socket.gaierror as e:
        return DNSLookupResult(
            host=hostname,
            status=DNSStatus.ERROR,
            error_message=f"DNS resolution failed: {e.strerror}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error resolving {hostname}: {e}", exc_info=True)
        return DNSLookupResult(
            host=hostname,
            status=DNSStatus.ERROR,
            error_message=f"Unexpected error: {str(e)}"
        )
```

#### Key Takeaways
- Validate inputs before network operations
- Distinguish between "not found" (expected) and errors (unexpected)
- IPv6 failures are non-fatal if IPv4 succeeds
- Reverse DNS is optional and doesn't fail the entire lookup
- Timeouts get specific error messages with remediation suggestions

### Port Utilities (`src/shared/port_utils.py`)

#### Status Codes
```python
class PortStatus(Enum):
    OPEN = "open"          # TCP connection succeeded
    CLOSED = "closed"      # Connection actively refused
    FILTERED = "filtered"  # No response (firewall likely blocking)
    TIMEOUT = "timeout"    # Connection attempt timed out
    ERROR = "error"        # Other errors (invalid host, network down)
```

#### Pattern: Port Connectivity Check

```python
def check_port_open(host: str, port: int, timeout: float = 3.0) -> PortCheckResult:
    """
    Check if a TCP port is open with detailed error classification.
    
    Args:
        host: Target hostname or IP
        port: Port number (1-65535)
        timeout: Connection timeout in seconds
    
    Returns:
        PortCheckResult with status and optional error message
    """
    # Validate inputs
    if not host:
        return PortCheckResult(
            host=host,
            port=port,
            status=PortStatus.ERROR,
            error_message="Host cannot be empty"
        )
    
    if not isinstance(port, int) or port < 1 or port > 65535:
        return PortCheckResult(
            host=host,
            port=port,
            status=PortStatus.ERROR,
            error_message=f"Port must be between 1-65535, got {port}"
        )
    
    start_time = time.time()
    sock = None
    
    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Attempt connection
        result = sock.connect_ex((host, port))
        response_time = (time.time() - start_time) * 1000
        
        if result == 0:
            # Port is open
            service_name = get_service_name(port)
            return PortCheckResult(
                host=host,
                port=port,
                status=PortStatus.OPEN,
                service_name=service_name,
                response_time_ms=response_time
            )
        else:
            # Connection refused (port closed)
            return PortCheckResult(
                host=host,
                port=port,
                status=PortStatus.CLOSED,
                response_time_ms=response_time
            )
    
    except socket.timeout:
        # Timeout suggests firewall filtering
        response_time = (time.time() - start_time) * 1000
        return PortCheckResult(
            host=host,
            port=port,
            status=PortStatus.FILTERED,
            response_time_ms=response_time,
            error_message=f"Connection timed out after {timeout}s (likely filtered by firewall)"
        )
    
    except socket.gaierror as e:
        # DNS resolution failed
        return PortCheckResult(
            host=host,
            port=port,
            status=PortStatus.ERROR,
            error_message=f"Cannot resolve hostname '{host}': {e.strerror}"
        )
    
    except OSError as e:
        # Network unreachable, host down, etc.
        return PortCheckResult(
            host=host,
            port=port,
            status=PortStatus.ERROR,
            error_message=f"Network error: {e.strerror}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error checking {host}:{port}: {e}", exc_info=True)
        return PortCheckResult(
            host=host,
            port=port,
            status=PortStatus.ERROR,
            error_message=f"Unexpected error: {str(e)}"
        )
    
    finally:
        # Always close socket
        if sock:
            try:
                sock.close()
            except Exception:
                pass  # Ignore errors during cleanup
```

#### Pattern: Concurrent Port Scanning with Error Aggregation

```python
def check_multiple_ports(
    host: str,
    ports: list[int],
    timeout: float = 3.0,
    max_workers: int = 10
) -> list[PortCheckResult]:
    """
    Scan multiple ports concurrently with individual error handling.
    
    Args:
        host: Target hostname or IP
        ports: List of port numbers to check
        timeout: Per-port timeout in seconds
        max_workers: Maximum concurrent threads
    
    Returns:
        List of PortCheckResult (one per port, never raises)
    """
    if not ports:
        return []
    
    results = []
    
    # Use ThreadPoolExecutor for concurrent scanning
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all port checks
        future_to_port = {
            executor.submit(check_port_open, host, port, timeout): port
            for port in ports
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_port):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                # Individual port check failed catastrophically
                port = future_to_port[future]
                logger.error(f"Thread error checking port {port}: {e}", exc_info=True)
                results.append(PortCheckResult(
                    host=host,
                    port=port,
                    status=PortStatus.ERROR,
                    error_message=f"Thread execution error: {str(e)}"
                ))
    
    # Sort by port number for consistent output
    return sorted(results, key=lambda r: r.port)
```

#### Key Takeaways
- Distinguish between CLOSED (connection refused) and FILTERED (timeout)
- Provide specific error messages for DNS failures vs network errors
- Always close sockets in finally blocks
- Handle thread execution errors in concurrent operations
- Validate port ranges before attempting connections

### Latency Utilities (`src/shared/latency_utils.py`)

#### Status Codes
```python
class LatencyStatus(Enum):
    SUCCESS = "success"        # Ping completed successfully
    UNREACHABLE = "unreachable"  # Host/network unreachable
    TIMEOUT = "timeout"        # All packets lost
    ERROR = "error"            # Command failed or parse error
```

#### Pattern: Cross-Platform Ping with Parsing

```python
def ping_statistics(
    host: str,
    count: int = 4,
    timeout: int = 5,
    interval: float = 1.0
) -> PingStatistics:
    """
    Execute ping and parse results with cross-platform support.
    
    Args:
        host: Target hostname or IP
        count: Number of ping packets
        timeout: Maximum wait time per packet
        interval: Time between packets
    
    Returns:
        PingStatistics with latency data or error status
    """
    # Validate inputs
    if not host:
        return PingStatistics(
            host=host,
            status=LatencyStatus.ERROR,
            error_message="Host cannot be empty"
        )
    
    if count < 1:
        return PingStatistics(
            host=host,
            status=LatencyStatus.ERROR,
            error_message=f"Count must be at least 1, got {count}"
        )
    
    # Build platform-specific ping command
    if platform.system().lower() == 'windows':
        cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
    else:  # Linux, macOS
        cmd = ['ping', '-c', str(count), '-W', str(timeout), '-i', str(interval), host]
    
    try:
        # Execute ping command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout * count + 10  # Allow extra time for subprocess
        )
        
        # Parse output based on platform
        if platform.system().lower() == 'windows':
            stats = _parse_ping_windows(result.stdout, result.stderr)
        else:
            stats = _parse_ping_unix(result.stdout, result.stderr)
        
        # Check if ping succeeded
        if stats['packets_received'] == 0:
            return PingStatistics(
                host=host,
                packets_sent=stats['packets_sent'],
                packets_received=0,
                packet_loss_percent=100.0,
                status=LatencyStatus.TIMEOUT,
                error_message=f"All {count} packets lost. Host may be down or blocking ICMP."
            )
        
        # Calculate jitter (standard deviation)
        if len(stats['individual_rtts']) > 1:
            mean = statistics.mean(stats['individual_rtts'])
            variance = statistics.variance(stats['individual_rtts'], mean)
            stddev = math.sqrt(variance)
        else:
            stddev = 0.0
        
        return PingStatistics(
            host=host,
            packets_sent=stats['packets_sent'],
            packets_received=stats['packets_received'],
            packet_loss_percent=stats['packet_loss_percent'],
            min_ms=stats['min_ms'],
            avg_ms=stats['avg_ms'],
            max_ms=stats['max_ms'],
            stddev_ms=stddev,
            individual_rtts=stats['individual_rtts'],
            status=LatencyStatus.SUCCESS
        )
    
    except subprocess.TimeoutExpired:
        return PingStatistics(
            host=host,
            status=LatencyStatus.TIMEOUT,
            error_message=f"Ping command timed out after {timeout * count + 10} seconds"
        )
    
    except FileNotFoundError:
        return PingStatistics(
            host=host,
            status=LatencyStatus.ERROR,
            error_message="Ping command not found. Ensure 'ping' is installed and in PATH."
        )
    
    except Exception as e:
        logger.error(f"Unexpected error pinging {host}: {e}", exc_info=True)
        return PingStatistics(
            host=host,
            status=LatencyStatus.ERROR,
            error_message=f"Unexpected error: {str(e)}"
        )

def _parse_ping_unix(stdout: str, stderr: str) -> dict:
    """Parse Unix/Linux/macOS ping output."""
    stats = {
        'packets_sent': 0,
        'packets_received': 0,
        'packet_loss_percent': 100.0,
        'min_ms': 0.0,
        'avg_ms': 0.0,
        'max_ms': 0.0,
        'individual_rtts': []
    }
    
    try:
        # Extract individual RTTs
        for line in stdout.split('\n'):
            match = re.search(r'time[=<](\d+\.?\d*)\s*ms', line)
            if match:
                stats['individual_rtts'].append(float(match.group(1)))
        
        # Extract summary statistics
        summary_match = re.search(
            r'(\d+) packets transmitted, (\d+) (?:packets )?received, ([\d.]+)% packet loss',
            stdout
        )
        if summary_match:
            stats['packets_sent'] = int(summary_match.group(1))
            stats['packets_received'] = int(summary_match.group(2))
            stats['packet_loss_percent'] = float(summary_match.group(3))
        
        # Extract min/avg/max
        rtt_match = re.search(r'min/avg/max[/\w]* = ([\d.]+)/([\d.]+)/([\d.]+)', stdout)
        if rtt_match:
            stats['min_ms'] = float(rtt_match.group(1))
            stats['avg_ms'] = float(rtt_match.group(2))
            stats['max_ms'] = float(rtt_match.group(3))
    
    except (ValueError, AttributeError) as e:
        logger.warning(f"Error parsing ping output: {e}")
    
    return stats
```

#### Key Takeaways
- Handle platform differences (Windows vs Unix) in command construction and parsing
- Provide fallback parsing when statistics lines are missing
- Distinguish between complete failure (all packets lost) and partial success
- Validate that required commands (ping, traceroute, mtr) are available
- Use subprocess timeouts to prevent hanging

## Best Practices

### 1. Input Validation

Always validate inputs before performing operations:

```python
def validate_inputs(host: str, port: int, timeout: float) -> Optional[str]:
    """
    Validate inputs and return error message if invalid.
    
    Returns:
        Error message string if invalid, None if valid
    """
    if not host or not isinstance(host, str):
        return "Host must be a non-empty string"
    
    if not isinstance(port, int) or not (1 <= port <= 65535):
        return f"Port must be an integer between 1-65535, got {port}"
    
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        return f"Timeout must be a positive number, got {timeout}"
    
    return None  # All valid
```

### 2. Resource Cleanup

Always clean up resources (sockets, file handles) using context managers or finally blocks:

```python
# ✅ GOOD - Using context manager
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(timeout)
    sock.connect((host, port))
    # Socket automatically closed

# ✅ GOOD - Using finally
sock = None
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
finally:
    if sock:
        sock.close()

# ❌ BAD - Socket may leak
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, port))
sock.close()  # Might not execute if connect raises
```

### 3. Timeout Configuration

Make all timeouts configurable with sensible defaults:

```python
def network_operation(
    host: str,
    timeout: int = 5,  # Sensible default
    retry_count: int = 3
) -> Result:
    """
    Perform network operation with configurable timeout.
    
    Default timeout of 5 seconds works for most cases,
    but users can increase for slow connections.
    """
    pass
```

### 4. Graceful Degradation

Provide partial results when full operation fails:

```python
def resolve_hostname(hostname: str) -> DNSLookupResult:
    ipv4_addresses = []
    ipv6_addresses = []
    
    # Try IPv4
    try:
        ipv4_addresses = get_ipv4_addresses(hostname)
    except Exception as e:
        logger.warning(f"IPv4 resolution failed: {e}")
    
    # Try IPv6 (independent of IPv4 result)
    try:
        ipv6_addresses = get_ipv6_addresses(hostname)
    except Exception as e:
        logger.warning(f"IPv6 resolution failed: {e}")
    
    # Return whatever we got
    if ipv4_addresses or ipv6_addresses:
        return DNSLookupResult(
            status=DNSStatus.SUCCESS,
            ipv4_addresses=ipv4_addresses,
            ipv6_addresses=ipv6_addresses
        )
    else:
        return DNSLookupResult(status=DNSStatus.NOT_FOUND)
```

### 5. User-Friendly Error Messages

Provide context and suggestions in error messages:

```python
# ✅ GOOD - Helpful and actionable
"DNS lookup timed out after 5 seconds. Try increasing timeout with timeout=10 or check your DNS server."

# ✅ GOOD - Explains what happened
"Port 443 is filtered (no response after 3s). This usually means a firewall is blocking the connection."

# ❌ BAD - Vague and unhelpful
"Operation failed"

# ❌ BAD - Technical jargon without context
"socket.gaierror: [Errno 11001] getaddrinfo failed"
```

### 6. Logging vs User Messages

Separate detailed error logging from user-facing messages:

```python
import logging

logger = logging.getLogger(__name__)

def risky_operation(host: str) -> Result:
    try:
        # Complex operation
        result = complex_network_call(host)
        return Result(status="success", data=result)
    
    except SpecificNetworkError as e:
        # Log full details for debugging
        logger.error(
            f"Network error in risky_operation for {host}",
            exc_info=True,
            extra={'host': host, 'error_code': e.code}
        )
        
        # Return simple message to user
        return Result(
            status="error",
            error_message="Network connection failed. Please check your internet connection."
        )
```

## Testing Error Handling

### Unit Test Patterns

Test all error paths using mocks:

```python
import unittest
from unittest.mock import patch, MagicMock
import socket

class TestDNSErrorHandling(unittest.TestCase):
    
    @patch('socket.getaddrinfo')
    def test_dns_timeout(self, mock_getaddrinfo):
        """Test that DNS timeout is handled correctly."""
        mock_getaddrinfo.side_effect = socket.timeout("Timed out")
        
        result = resolve_hostname('example.com', timeout=5)
        
        self.assertEqual(result.status, DNSStatus.TIMEOUT)
        self.assertIn("timed out", result.error_message.lower())
        self.assertIsNone(result.ipv4_addresses)
    
    @patch('socket.getaddrinfo')
    def test_dns_not_found(self, mock_getaddrinfo):
        """Test NXDOMAIN handling."""
        error = socket.gaierror(socket.EAI_NONAME, "Name or service not known")
        mock_getaddrinfo.side_effect = error
        
        result = resolve_hostname('nonexistent.invalid')
        
        self.assertEqual(result.status, DNSStatus.NOT_FOUND)
        self.assertIn("not found", result.error_message.lower())
    
    def test_invalid_hostname(self):
        """Test empty hostname validation."""
        result = resolve_hostname('')
        
        self.assertEqual(result.status, DNSStatus.ERROR)
        self.assertIn("empty", result.error_message.lower())
```

### Integration Test Patterns

Test real error scenarios:

```python
class TestPortScanningIntegration(unittest.TestCase):
    
    def test_unreachable_host(self):
        """Test scanning a known unreachable IP."""
        # 192.0.2.1 is reserved for documentation (TEST-NET-1)
        result = check_port_open('192.0.2.1', 80, timeout=1)
        
        # Should timeout or error, not crash
        self.assertIn(result.status, [PortStatus.TIMEOUT, PortStatus.FILTERED, PortStatus.ERROR])
    
    def test_closed_port_on_localhost(self):
        """Test scanning a closed port on localhost."""
        # Port 1 should be closed on most systems
        result = check_port_open('127.0.0.1', 1, timeout=2)
        
        self.assertEqual(result.status, PortStatus.CLOSED)
    
    def test_invalid_port_range(self):
        """Test port number validation."""
        result = check_port_open('127.0.0.1', 70000, timeout=2)
        
        self.assertEqual(result.status, PortStatus.ERROR)
        self.assertIn("65535", result.error_message)
```

## Common Pitfalls

### 1. Swallowing Exceptions

```python
# ❌ BAD - Silently fails
try:
    result = dangerous_operation()
except:
    pass  # User has no idea something went wrong

# ✅ GOOD - Log and return error status
try:
    result = dangerous_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    return ErrorResult(message="Operation failed. Check logs for details.")
```

### 2. Overly Broad Exception Catching

```python
# ❌ BAD - Catches everything including KeyboardInterrupt
try:
    result = operation()
except:
    handle_error()

# ✅ GOOD - Catch specific exceptions
try:
    result = operation()
except (socket.timeout, socket.gaierror) as e:
    handle_network_error(e)
except Exception as e:
    handle_unexpected_error(e)
```

### 3. Not Cleaning Up Resources

```python
# ❌ BAD - File handle leaks if operation raises
file = open('data.txt')
process_file(file)
file.close()

# ✅ GOOD - Always cleaned up
with open('data.txt') as file:
    process_file(file)
```

### 4. Exposing Internal Details in Error Messages

```python
# ❌ BAD - Exposes stack trace to users
except Exception as e:
    return f"Error: {traceback.format_exc()}"

# ✅ GOOD - User-friendly message, detailed logging
except Exception as e:
    logger.error("Operation failed", exc_info=True)
    return "Operation failed. Please contact support if this persists."
```

### 5. Forgetting to Set Timeouts

```python
# ❌ BAD - Can hang forever
sock = socket.socket()
sock.connect((host, port))  # No timeout!

# ✅ GOOD - Always set timeout
sock = socket.socket()
sock.settimeout(5.0)
sock.connect((host, port))
```

## Error Handling Checklist

When implementing a new network operation, ensure:

- [ ] Input validation with helpful error messages
- [ ] Configurable timeout with sensible default
- [ ] Try-except blocks around all network calls
- [ ] Specific exception handling (avoid bare `except:`)
- [ ] Resource cleanup using `finally` or context managers
- [ ] Appropriate status enum value returned
- [ ] User-friendly error message (not raw exception text)
- [ ] Detailed error logging for debugging
- [ ] Unit tests for all error paths
- [ ] Integration test for real-world failure scenarios
- [ ] Docstring documenting possible error returns

## Reference Implementation

See these files for comprehensive error handling examples:

- **[src/shared/dns_utils.py](src/shared/dns_utils.py)** - DNS error handling patterns
- **[src/shared/port_utils.py](src/shared/port_utils.py)** - Port scanning error handling
- **[src/shared/latency_utils.py](src/shared/latency_utils.py)** - Cross-platform command error handling
- **[tests/test_phase3_diagnostics.py](tests/test_phase3_diagnostics.py)** - Error handling test patterns

## Further Reading

- **[PHASE3-QUICK-START.md](PHASE3-QUICK-START.md)** - Practical usage examples
- **[docs/PHASE3_DIAGNOSTICS.md](docs/PHASE3_DIAGNOSTICS.md)** - Complete API reference
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines
- **Python Documentation**: [Built-in Exceptions](https://docs.python.org/3/library/exceptions.html)
- **Python Documentation**: [socket Module](https://docs.python.org/3/library/socket.html)

---

**Questions or suggestions?** Open an issue or discussion on [GitHub](https://github.com/knowoneactual/Network-Triage-Tool)!

**Last Updated:** December 19, 2025 (Phase 3)
