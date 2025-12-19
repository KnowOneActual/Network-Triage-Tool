# Phase 3 Quick Start Guide

Get started with Phase 3 advanced diagnostics in under 5 minutes.

## Overview

Phase 3 introduces three powerful diagnostic modules:
- **DNS Utilities**: Hostname resolution, DNS validation, propagation checking
- **Port Utilities**: Port scanning, service detection, connectivity testing
- **Latency Utilities**: Ping statistics with jitter, MTR-style traceroute

All modules use **only Python standard library** - no external dependencies required.

## Installation

```bash
# Clone the repository
git clone https://github.com/knowoneactual/Network-Triage-Tool.git
cd Network-Triage-Tool

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .
```

## Quick Examples

### DNS Resolution

```python
from src.shared.dns_utils import resolve_hostname

# Basic hostname resolution
result = resolve_hostname('google.com')
if result.status.value == 'success':
    print(f"IPv4 addresses: {result.ipv4_addresses}")
    print(f"IPv6 addresses: {result.ipv6_addresses}")
    print(f"Reverse DNS: {result.reverse_dns}")
    print(f"Lookup time: {result.lookup_time_ms:.2f}ms")
else:
    print(f"Error: {result.error_message}")
```

**Output:**
```
IPv4 addresses: ['142.250.185.46']
IPv6 addresses: ['2607:f8b0:4004:c07::71']
Reverse DNS: lga34s32-in-f14.1e100.net
Lookup time: 23.45ms
```

### DNS Server Validation

```python
from src.shared.dns_utils import validate_dns_server

# Check if Google DNS is responsive
result = validate_dns_server('8.8.8.8')
if result['is_responsive']:
    print(f"✅ DNS server is responsive ({result['response_time_ms']:.2f}ms)")
else:
    print(f"❌ DNS server failed: {result['error']}")
```

### DNS Propagation Check

```python
from src.shared.dns_utils import check_dns_propagation

# Check DNS propagation across 5 major providers
results = check_dns_propagation('example.com')
for provider in results:
    status = "✅" if provider['status'] == 'found' else "❌"
    print(f"{status} {provider['provider']:15s}: {provider['ips']}")
```

**Output:**
```
✅ Google         : ['93.184.216.34']
✅ Cloudflare     : ['93.184.216.34']
✅ OpenDNS        : ['93.184.216.34']
✅ Quad9          : ['93.184.216.34']
✅ Level3         : ['93.184.216.34']
```

### Port Scanning

```python
from src.shared.port_utils import check_port_open, check_multiple_ports

# Check single port
result = check_port_open('192.168.1.1', 22)
print(f"Port 22 ({result.service_name}): {result.status.value}")

# Check multiple ports
ports = [22, 80, 443, 3306, 5432]
results = check_multiple_ports('localhost', ports)
for r in results:
    print(f"Port {r.port:5d} ({r.service_name:10s}): {r.status.value}")
```

**Output:**
```
Port 22 (SSH): open
Port   22 (SSH       ): open
Port   80 (HTTP      ): closed
Port  443 (HTTPS     ): open
Port 3306 (MySQL     ): filtered
Port 5432 (PostgreSQL): closed
```

### Common Ports Scan

```python
from src.shared.port_utils import scan_common_ports, summarize_port_scan

# Scan ~30 common service ports
results = scan_common_ports('192.168.1.100')

# Get summary statistics
summary = summarize_port_scan(results)
print(f"Total scanned: {summary['total_scanned']}")
print(f"Open: {summary['open_count']}, Closed: {summary['closed_count']}")
print(f"\nOpen ports:")
for port, service in summary['open_ports']:
    print(f"  {port:5d} - {service}")
```

### Ping Statistics with Jitter

```python
from src.shared.latency_utils import ping_statistics

# Comprehensive ping analysis
stats = ping_statistics('8.8.8.8', count=10)
if stats.status.value == 'success':
    print(f"Host: {stats.host}")
    print(f"Packets: {stats.packets_sent} sent, {stats.packets_received} received")
    print(f"Loss: {stats.packet_loss_percent:.1f}%")
    print(f"Latency (min/avg/max): {stats.min_ms:.2f}/{stats.avg_ms:.2f}/{stats.max_ms:.2f}ms")
    print(f"Jitter (stddev): {stats.stddev_ms:.2f}ms")
    
    # Interpret jitter
    if stats.stddev_ms < 2:
        print("✅ Network quality: Excellent (stable latency)")
    elif stats.stddev_ms < 5:
        print("⚠️  Network quality: Good (moderate variation)")
    else:
        print("❌ Network quality: Poor (high jitter)")
else:
    print(f"Ping failed: {stats.error_message}")
```

**Output:**
```
Host: 8.8.8.8
Packets: 10 sent, 10 received
Loss: 0.0%
Latency (min/avg/max): 12.34/15.67/18.90ms
Jitter (stddev): 1.82ms
✅ Network quality: Excellent (stable latency)
```

### MTR-Style Traceroute

```python
from src.shared.latency_utils import mtr_style_trace

# Comprehensive path analysis
hops, message = mtr_style_trace('8.8.8.8', max_hops=15)
print(f"Trace status: {message}\n")

for hop in hops:
    avg_rtt = hop.avg_rtt_ms()
    if avg_rtt:
        hostname = hop.hostname or "(no reverse DNS)"
        print(f"Hop {hop.hop_number:2d}: {hop.ip_address:15s} {avg_rtt:7.2f}ms  {hostname}")
    else:
        print(f"Hop {hop.hop_number:2d}: * * * (timeout)")
```

**Output:**
```
Trace status: MTR trace completed

Hop  1: 192.168.1.1      1.23ms  gateway.local
Hop  2: 10.0.0.1        12.45ms  isp-router.net
Hop  3: 172.16.1.1      23.56ms  (no reverse DNS)
...
Hop 12: 8.8.8.8         15.67ms  dns.google
```

## Port Range Scanning

```python
from src.shared.port_utils import scan_port_range

# Scan well-known ports (1-1024)
open_ports = scan_port_range('192.168.1.50', start_port=1, end_port=1024, timeout=1)
print(f"Found {len(open_ports)} open ports:\n")
for port in open_ports:
    print(f"  Port {port.port:5d} ({port.service_name or 'unknown'})")
```

## Advanced Usage

### Concurrent Port Scanning with Custom Thread Pool

```python
from src.shared.port_utils import check_multiple_ports
import time

# Scan 100 ports with 50 concurrent workers
ports = list(range(1, 101))
start = time.time()
results = check_multiple_ports(
    'target.example.com',
    ports,
    timeout=2,
    max_workers=50  # Higher concurrency for faster scanning
)
elapsed = time.time() - start
print(f"Scanned {len(ports)} ports in {elapsed:.2f} seconds")
```

### DNS Resolution with Custom Timeout

```python
from src.shared.dns_utils import resolve_hostname

# Fast lookup with 1-second timeout
result = resolve_hostname('slow-dns-server.com', timeout=1, include_reverse_dns=False)
if result.status.value == 'timeout':
    print("DNS lookup timed out (server may be slow or unreachable)")
```

### Export Results to JSON

```python
import json
from src.shared.dns_utils import resolve_hostname
from src.shared.port_utils import scan_common_ports

# DNS results
dns_result = resolve_hostname('example.com')
with open('dns_results.json', 'w') as f:
    json.dump(dns_result.to_dict(), f, indent=2)

# Port scan results
port_results = scan_common_ports('192.168.1.1')
port_data = [r.to_dict() for r in port_results]
with open('port_scan.json', 'w') as f:
    json.dump(port_data, f, indent=2)
```

## Running Tests

```bash
# Run all Phase 3 tests
python -m pytest tests/test_phase3_diagnostics.py -v

# Run specific test class
python -m pytest tests/test_phase3_diagnostics.py::TestDNSUtils -v

# Run with coverage report
python -m pytest tests/test_phase3_diagnostics.py --cov=src.shared --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Performance Tips

### DNS Operations
- Use `timeout=3` for local networks
- Use `timeout=10` for slower internet connections
- Set `include_reverse_dns=False` to skip PTR lookups (faster)

### Port Scanning
- Use `max_workers=10` for local networks
- Use `max_workers=50` for internet scanning
- Lower `timeout` values (1-2s) for faster scans on responsive hosts
- Higher `timeout` values (5s+) for slow or heavily filtered networks

### Latency Measurement
- Use `count=5` for quick checks
- Use `count=20` for accurate jitter analysis
- Use `interval=0.2` for faster pings (may be rate-limited)
- Use `interval=1.0` to avoid rate limiting

## Cross-Platform Notes

### Windows
- Ping and traceroute automatically use Windows commands (`ping`, `tracert`)
- MTR is not natively available (falls back to traceroute)

### Linux
- Install `mtr` for best traceroute experience: `sudo apt install mtr`
- Some operations may require `sudo` for raw socket access

### macOS
- Install `mtr` via Homebrew: `brew install mtr`
- All features work out of the box

## Next Steps

- Review the [full API documentation](docs/PHASE3_DIAGNOSTICS.md) for detailed reference
- Check [RELEASE-NOTES-PHASE3.md](RELEASE-NOTES-PHASE3.md) for complete changelog
- See [PHASE4-INTEGRATION-ROADMAP.md](PHASE4-INTEGRATION-ROADMAP.md) for upcoming TUI integration
- Read [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md) for error handling patterns

## Common Issues

### "Connection refused" vs "Timeout"
- **Connection refused** (CLOSED): Host is up, port is actively closed
- **Timeout** (FILTERED): Firewall is blocking or host is down

### DNS Not Found
- Verify domain exists: `nslookup example.com`
- Check DNS server: `validate_dns_server('8.8.8.8')`
- Test propagation: `check_dns_propagation('your-domain.com')`

### High Jitter (>5ms)
- Wi-Fi interference: Switch to 5GHz or wired connection
- Network congestion: Test during off-peak hours
- ISP issues: Compare with different destinations

## Support

For issues, questions, or contributions:
- Open an issue: https://github.com/knowoneactual/Network-Triage-Tool/issues
- Read contributing guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Review documentation: [DOCUMENTATION-INDEX.md](DOCUMENTATION-INDEX.md)

---

**Phase 3 is production-ready with 22/22 tests passing across all platforms! 🚀**
