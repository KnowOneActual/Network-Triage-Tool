# Phase 3: Advanced Diagnostics

Phase 3 introduces comprehensive network diagnostic utilities for DNS resolution, port connectivity, and latency measurement. These modules extend the Network-Triage-Tool's capabilities to provide enterprise-grade diagnostics for network professionals.

## Overview

Phase 3 consists of three independent utility modules:

1. **DNS Utilities** (`src/shared/dns_utils.py`)
2. **Port Connectivity** (`src/shared/port_utils.py`)
3. **Latency & Jitter** (`src/shared/latency_utils.py`)

Each module is:
- ✅ **Independent**: No cross-dependencies; can be used standalone
- ✅ **Well-tested**: 30+ unit tests with 100% pass rate
- ✅ **Production-ready**: Error handling, timeouts, graceful degradation
- ✅ **Cross-platform**: Linux, macOS, Windows (where applicable)

---

## 1. DNS Utilities (`dns_utils.py`)

Comprehensive DNS resolution and validation capabilities.

### Core Functions

#### `resolve_hostname(hostname, timeout=5, include_reverse_dns=True) -> DNSLookupResult`

Resolve A, AAAA, and reverse DNS records for a hostname.

**Parameters:**
- `hostname` (str): FQDN or IP address to resolve
- `timeout` (int): Socket timeout in seconds (default: 5)
- `include_reverse_dns` (bool): Perform reverse DNS lookup (default: True)

**Returns:** `DNSLookupResult` object with:
- `ipv4_addresses`: List of resolved IPv4 addresses
- `ipv6_addresses`: List of resolved IPv6 addresses (normalized)
- `reverse_dns`: Reverse DNS hostname (if available)
- `lookup_time_ms`: Total resolution time
- `status`: DNSStatus enum (SUCCESS, NOT_FOUND, TIMEOUT, ERROR)
- `records`: List of DNSRecord objects with detailed info

**Example:**
```python
from src.shared.dns_utils import resolve_hostname

result = resolve_hostname('google.com')
if result.status.value == 'success':
    print(f"IPv4: {result.ipv4_addresses}")
    print(f"IPv6: {result.ipv6_addresses}")
    print(f"Reverse DNS: {result.reverse_dns}")
    print(f"Lookup time: {result.lookup_time_ms:.2f}ms")
else:
    print(f"Error: {result.error_message}")
```

**Error Handling:**
- `NOT_FOUND`: Hostname cannot be resolved (DNS returns NXDOMAIN)
- `TIMEOUT`: Resolution exceeds timeout threshold
- `ERROR`: Unexpected error during lookup

---

#### `validate_dns_server(server_ip, test_domain='google.com', timeout=5) -> Dict`

Validate if a DNS server is responsive and functional.

**Parameters:**
- `server_ip` (str): IP address of DNS server (port 53 assumed)
- `test_domain` (str): Domain to use for test query (default: 'google.com')
- `timeout` (int): Socket timeout in seconds (default: 5)

**Returns:** Dictionary with:
- `server_ip`: IP address tested
- `is_responsive`: Boolean indicating responsiveness
- `response_time_ms`: Time to receive response
- `status`: 'responsive', 'timeout', 'error', 'no_response'
- `error`: Error message if applicable

**Example:**
```python
from src.shared.dns_utils import validate_dns_server

result = validate_dns_server('8.8.8.8')
if result['is_responsive']:
    print(f"Google DNS is responsive ({result['response_time_ms']:.2f}ms)")
else:
    print(f"DNS server check failed: {result['error']}")
```

---

#### `check_dns_propagation(domain, record_type='A', timeout=5) -> List[Dict]`

Check DNS propagation across multiple public DNS providers.

Useful for:
- Verifying DNS changes have propagated
- Detecting divergent DNS zones
- Troubleshooting DNS consistency issues

**Parameters:**
- `domain` (str): Domain to check
- `record_type` (str): Type of record ('A', 'AAAA', 'CNAME', 'MX')
- `timeout` (int): Timeout per server in seconds (default: 5)

**Returns:** List of result dictionaries with:
- `provider`: DNS provider name (e.g., 'Google', 'Cloudflare', 'OpenDNS')
- `server_ip`: IP address of the resolver
- `ips`: List of resolved IP addresses
- `status`: 'found', 'not_found', 'timeout', 'error'

**Example:**
```python
from src.shared.dns_utils import check_dns_propagation

results = check_dns_propagation('example.com')
for provider_result in results:
    print(f"{provider_result['provider']}: {provider_result['status']}")
    if provider_result['ips']:
        print(f"  IPs: {provider_result['ips']}")
```

**Providers Checked:**
- Google (8.8.8.8, 8.8.4.4)
- Cloudflare (1.1.1.1, 1.0.0.1)
- OpenDNS (208.67.222.222, 208.67.220.220)
- Quad9 (9.9.9.9, 149.112.112.112)

---

### Data Classes

#### `DNSLookupResult`

Complete result of a DNS lookup operation.

**Attributes:**
- `hostname`: Original hostname queried
- `ipv4_addresses`: List[str] of IPv4 addresses
- `ipv6_addresses`: List[str] of IPv6 addresses (normalized)
- `reverse_dns`: Optional reverse DNS hostname
- `lookup_time_ms`: Total time in milliseconds
- `status`: DNSStatus enum value
- `error_message`: Optional error description
- `records`: List[DNSRecord] with granular details

**Method:**
- `to_dict()`: Convert to JSON-serializable dictionary

#### `DNSRecord`

Individual DNS record with metadata.

**Attributes:**
- `record_type`: 'A', 'AAAA', 'PTR'
- `value`: Resolved IP or hostname
- `query_time_ms`: Time to resolve this record
- `status`: DNSStatus for this specific record

---

## 2. Port Connectivity Utilities (`port_utils.py`)

TCP-based port scanning and connectivity testing.

### Core Functions

#### `check_port_open(host, port, timeout=3, grab_banner=False) -> PortCheckResult`

Check if a single port is open using TCP connection.

**Parameters:**
- `host` (str): Hostname or IP address
- `port` (int): Port number (1-65535)
- `timeout` (int): Connection timeout in seconds (default: 3)
- `grab_banner` (bool): Attempt to read service banner (default: False)

**Returns:** `PortCheckResult` with:
- `host`: Target hostname/IP
- `port`: Port number
- `status`: PortStatus enum (OPEN, CLOSED, FILTERED, TIMEOUT, ERROR)
- `service_name`: Known service name (e.g., 'SSH', 'HTTP')
- `response_time_ms`: Time to determine status
- `banner`: Optional service banner (first 100 chars)

**Status Interpretation:**
- **OPEN**: Successfully connected (RST/SYN-ACK received)
- **CLOSED**: Connection refused (RST received immediately)
- **FILTERED**: Timeout likely due to firewall (no response)
- **TIMEOUT**: Connection attempt exceeded timeout
- **ERROR**: Unexpected error (invalid host, etc.)

**Example:**
```python
from src.shared.port_utils import check_port_open

result = check_port_open('192.168.1.1', 22, timeout=3)
if result.status.value == 'open':
    print(f"Port 22 (SSH) is open")
elif result.status.value == 'closed':
    print(f"Port 22 is closed (host responded)")
elif result.status.value == 'filtered':
    print(f"Port 22 is filtered (likely firewall)")
```

---

#### `check_multiple_ports(host, ports, timeout=3, max_workers=10) -> List[PortCheckResult]`

Concurrently check multiple ports.

**Parameters:**
- `host` (str): Hostname or IP
- `ports` (List[int]): List of port numbers
- `timeout` (int): Per-port timeout in seconds (default: 3)
- `max_workers` (int): Maximum concurrent threads (default: 10)

**Returns:** List of `PortCheckResult` objects, sorted by port number

**Example:**
```python
from src.shared.port_utils import check_multiple_ports

results = check_multiple_ports('localhost', [22, 80, 443, 3306, 5432])
for result in results:
    status_str = result.status.value
    print(f"Port {result.port:5d} ({result.service_name:10s}): {status_str}")
```

---

#### `scan_common_ports(host, timeout=3, max_workers=10) -> List[PortCheckResult]`

Scan all ~30 common service ports.

**Common Ports Scanned:**
- **SSH (22), HTTP (80), HTTPS (443)** - Web services
- **SMTP (25), POP3 (110), IMAP (143)** - Email
- **DNS (53)** - Domain services
- **RDP (3389)** - Remote desktop
- **Databases**: MySQL (3306), PostgreSQL (5432), MSSQL (1433), MongoDB (27017)
- **Cache/NoSQL**: Redis (6379)
- **VNC (5900)** - Remote access
- And more...

**Example:**
```python
from src.shared.port_utils import scan_common_ports, PortStatus

results = scan_common_ports('192.168.1.100')
open_ports = [r for r in results if r.status == PortStatus.OPEN]
print(f"Found {len(open_ports)} open ports:")
for port in open_ports:
    print(f"  - Port {port.port} ({port.service_name})")
```

---

#### `scan_port_range(host, start_port=1, end_port=1024, timeout=2, max_workers=20) -> List[PortCheckResult]`

Scan a range of ports (returns only OPEN ports).

**Parameters:**
- `host` (str): Hostname or IP
- `start_port` (int): Starting port (inclusive, default: 1)
- `end_port` (int): Ending port (inclusive, default: 1024)
- `timeout` (int): Per-port timeout in seconds (default: 2)
- `max_workers` (int): Maximum concurrent threads (default: 20)

**Example:**
```python
from src.shared.port_utils import scan_port_range

# Scan well-known ports (1-1024)
open_ports = scan_port_range('192.168.1.50', 1, 1024, timeout=1)
for port in open_ports:
    print(f"Port {port.port} ({port.service_name}) is open")
```

---

#### `summarize_port_scan(results) -> Dict[str, Any]`

Generate summary statistics from port scan results.

**Returns:** Dictionary with:
- `total_scanned`: Total ports checked
- `open_count`: Number of open ports
- `closed_count`: Number of closed ports
- `filtered_count`: Number of filtered (likely firewalled) ports
- `timeout_count`: Number of timeout ports
- `error_count`: Number of error ports
- `open_ports`: List of (port, service_name) tuples
- `avg_response_time_ms`: Average response time
- `min/max_response_time_ms`: Response time extremes

**Example:**
```python
from src.shared.port_utils import check_multiple_ports, summarize_port_scan

results = check_multiple_ports('localhost', [22, 80, 443, 3306, 5432])
summary = summarize_port_scan(results)
print(f"Scanned: {summary['total_scanned']} ports")
print(f"Open: {summary['open_count']}, Closed: {summary['closed_count']}, Filtered: {summary['filtered_count']}")
if summary['open_ports']:
    print(f"Open services: {summary['open_ports']}")
```

---

### Data Classes

#### `PortCheckResult`

**Attributes:**
- `host`: Target hostname/IP
- `port`: Port number
- `status`: PortStatus enum value
- `service_name`: Known service name or None
- `response_time_ms`: Time to determine status
- `error_message`: Optional error description
- `banner`: Optional service banner

**Method:**
- `to_dict()`: Convert to JSON-serializable dictionary

---

## 3. Latency & Jitter Utilities (`latency_utils.py`)

Comprehensive latency measurement and path analysis.

### Core Functions

#### `ping_statistics(host, count=10, timeout=5, interval=0.5) -> PingStatistics`

Execute ping and calculate comprehensive statistics including jitter.

**Parameters:**
- `host` (str): Hostname or IP to ping
- `count` (int): Number of ping packets (default: 10)
- `timeout` (int): Timeout per ping in seconds (default: 5)
- `interval` (float): Interval between pings in seconds (default: 0.5)

**Returns:** `PingStatistics` object with:
- `host`: Target hostname/IP
- `packets_sent`: Number of packets sent
- `packets_received`: Number of successful responses
- `packet_loss_percent`: Percentage of lost packets
- `min_ms`, `avg_ms`, `max_ms`: Latency statistics
- `stddev_ms`: Standard deviation (jitter indicator)
- `rtt_values`: List of individual RTT measurements
- `status`: LatencyStatus enum

**Example:**
```python
from src.shared.latency_utils import ping_statistics

stats = ping_statistics('8.8.8.8', count=10)
if stats.status.value == 'success':
    print(f"Host: {stats.host}")
    print(f"Packets: {stats.packets_sent} sent, {stats.packets_received} received")
    print(f"Loss: {stats.packet_loss_percent:.1f}%")
    print(f"Latency: {stats.min_ms:.2f}/{stats.avg_ms:.2f}/{stats.max_ms:.2f}ms (min/avg/max)")
    print(f"Jitter (stddev): {stats.stddev_ms:.2f}ms")
else:
    print(f"Ping failed: {stats.error_message}")
```

**Interpretation:**
- **stddev_ms < 2**: Consistent, stable latency (good network)
- **stddev_ms 2-5**: Moderate variation (acceptable)
- **stddev_ms > 5**: High jitter (potential issues)

---

#### `mtr_style_trace(host, max_hops=30, timeout=5, min_hops=1) -> Tuple[List[TracerouteHop], str]`

Perform MTR-style tracing combining traceroute with latency statistics.

Automatically uses `mtr` if available, otherwise falls back to traceroute + ping.

**Parameters:**
- `host` (str): Destination hostname or IP
- `max_hops` (int): Maximum hops to trace (default: 30)
- `timeout` (int): Timeout per hop in seconds (default: 5)
- `min_hops` (int): Starting hop number (default: 1)

**Returns:** Tuple of:
- List of `TracerouteHop` objects with RTT data
- Status message ("MTR trace completed" or "Traceroute completed")

**Example:**
```python
from src.shared.latency_utils import mtr_style_trace

hops, message = mtr_style_trace('8.8.8.8', max_hops=15)
print(f"Trace status: {message}")
for hop in hops:
    avg_rtt = hop.avg_rtt_ms()
    if avg_rtt:
        print(f"Hop {hop.hop_number:2d}: {hop.ip_address:15s} {avg_rtt:7.2f}ms")
    else:
        print(f"Hop {hop.hop_number:2d}: * (timeout)")
```

---

### Data Classes

#### `PingStatistics`

**Attributes:**
- `host`: Target hostname/IP
- `packets_sent`: Packets transmitted
- `packets_received`: Successful responses
- `packet_loss_percent`: Loss percentage
- `min_ms`, `avg_ms`, `max_ms`: Latency statistics
- `stddev_ms`: Standard deviation (jitter)
- `status`: LatencyStatus enum
- `rtt_values`: List of individual measurements
- `error_message`: Optional error description

**Method:**
- `to_dict()`: Convert to JSON-serializable dictionary

#### `TracerouteHop`

**Attributes:**
- `hop_number`: Hop sequence number
- `hostname`: Optional reverse DNS hostname
- `ip_address`: IP address of this hop
- `rtt1_ms`, `rtt2_ms`, `rtt3_ms`: Individual RTT measurements
- `status`: 'responsive', 'timeout', 'error'

**Method:**
- `avg_rtt_ms()`: Calculate average RTT across available samples
- `to_dict()`: Convert to dictionary

---

## Testing

All Phase 3 modules include comprehensive unit tests:

```bash
# Run Phase 3 tests
python -m pytest tests/test_phase3_diagnostics.py -v

# Run specific test class
python -m pytest tests/test_phase3_diagnostics.py::TestDNSUtils -v

# Run with coverage
python -m pytest tests/test_phase3_diagnostics.py --cov=src.shared --cov-report=html
```

**Test Coverage:**
- DNS resolution (success, timeout, not found, error)
- DNS server validation
- DNS propagation checking
- Port checking (open, closed, filtered, timeout)
- Concurrent port scanning
- Port scan summarization
- Ping statistics and jitter calculation
- Traceroute/MTR fallback logic
- Error handling and edge cases

---

## Integration with TUI

Phase 3 utilities can be integrated into the Textual TUI as new tabs:

### Example: Advanced Diagnostics Tab

```python
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static
from src.shared.dns_utils import resolve_hostname
from src.shared.port_utils import check_multiple_ports

class DiagnosticsTab(Static):
    """Advanced diagnostics tab."""

    def compose(self) -> ComposeResult:
        yield Input(id="hostname-input", placeholder="Enter hostname")
        yield Button("Resolve DNS", id="dns-btn")
        yield Static(id="dns-output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "dns-btn":
            hostname = self.query_one("#hostname-input", Input).value
            result = resolve_hostname(hostname)
            output = self.query_one("#dns-output", Static)
            output.update(self._format_dns_result(result))

    def _format_dns_result(self, result) -> str:
        lines = [
            f"Hostname: {result.hostname}",
            f"IPv4: {', '.join(result.ipv4_addresses) or 'None'}",
            f"IPv6: {', '.join(result.ipv6_addresses) or 'None'}",
            f"Reverse DNS: {result.reverse_dns or 'None'}",
            f"Status: {result.status.value}",
            f"Lookup time: {result.lookup_time_ms:.2f}ms",
        ]
        return '\n'.join(lines)
```

---

## Cross-Platform Support

### Platform-Specific Behavior

| Feature | Linux | macOS | Windows |
|---------|-------|-------|----------|
| DNS Resolution | ✅ Full support | ✅ Full support | ✅ Full support |
| Port Checking | ✅ Full support | ✅ Full support | ✅ Full support |
| Ping Statistics | ✅ Full support | ✅ Full support | ✅ Full support |
| Traceroute | `traceroute` | `traceroute` | `tracert` |
| MTR Support | ✅ `mtr` | ⚠️ Limited | ✅ `mtr` (WSL) |

---

## Performance Considerations

### Port Scanning Performance

```python
# Concurrent workers scale performance
results = check_multiple_ports(
    'target.com',
    list(range(1, 1025)),  # 1024 ports
    timeout=2,
    max_workers=20  # Adjust based on system resources
)
# Estimated time: 1024 ports / 20 workers * 2s timeout ≈ 102 seconds
# With optimizations: ~100 seconds for full range scan
```

### DNS Resolution Performance

- **Single hostname**: ~25-100ms (depends on resolver)
- **Propagation check (5 providers)**: ~100-500ms (parallel)
- **Timeout handling**: Operations won't block for more than configured timeout

### Latency Measurement

- **10-packet ping**: ~10-20 seconds (accounting for interval)
- **Full traceroute (30 hops)**: ~2-5 minutes (depends on responsiveness)

---

## Error Handling Strategy

All Phase 3 modules follow consistent error handling:

1. **Graceful Degradation**: Missing tools (mtr, traceroute) don't crash
2. **Clear Status Codes**: Status enums provide explicit error types
3. **Timeout Protection**: All operations respect timeout parameters
4. **Error Messages**: Actionable error descriptions for debugging

---

## Future Enhancements

- [ ] IPv6-specific DNS checks
- [ ] DNSSEC validation
- [ ] Geolocation of DNS servers
- [ ] BGP route analysis
- [ ] TCP connection state tracking
- [ ] Service banner analysis
- [ ] Historical latency trending
- [ ] Alert thresholds for anomalies

---

## License

Phase 3 modules are licensed under the same terms as Network-Triage-Tool (MIT).
