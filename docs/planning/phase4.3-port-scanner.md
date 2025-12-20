# Phase 4.3: Port Scanner Widget Implementation Guide

**Status:** In Development  
**Started:** December 20, 2025  
**Target:** Complete by December 24, 2025  

## Overview

Phase 4.3 implements the **Port Scanner Widget**, which integrates Phase 3's comprehensive port scanning utilities into the Textual TUI. This widget follows the exact same architecture as the successful Phase 4.2 DNS Resolver Widget and leverages the same Foundation framework.

## Architecture

The Port Scanner Widget follows a consistent pattern established in Phase 4.1 & 4.2:

```
PortScannerWidget (Extends BaseWidget)
├── Input Management
│   ├── Target Host Input (validated)
│   ├── Scan Mode Selector (common/single/multiple/range)
│   ├── Port Input Parser
│   └── Timeout Configuration
├── Scan Execution
│   ├── Uses Phase 3 check_multiple_ports()
│   ├── Concurrent scanning (10 workers)
│   └── Progress feedback
├── Results Display
│   ├── Port Status (color-coded)
│   ├── Service Name (from COMMON_SERVICE_PORTS)
│   ├── Response Time (ms)
│   └── Summary Statistics
└── Error Handling
    ├── Input validation
    ├── DNS resolution errors
    └── Timeout/connectivity errors
```

## Implementation Details

### File Structure

```
src/tui/widgets/
├── port_scanner_widget.py     ← NEW (13KB)
├── dns_resolver_widget.py     (reference implementation)
├── base.py                    (foundation)
└── components.py              (shared UI components)

tests/
├── test_phase4_port_scanner_widget.py  ← NEW (31 tests)
└── test_phase4_dns_widget.py           (reference)
```

### Core Functionality

#### 1. Port Input Parsing

The `parse_ports_input()` method handles four scanning modes:

**Single Port Mode:**
```python
widget.parse_ports_input("80", "single")
# Returns: [80]
```

**Multiple Ports Mode:**
```python
widget.parse_ports_input("80,443,22", "multiple")
# Returns: [22, 80, 443]  # Sorted and deduplicated
```

**Port Range Mode:**
```python
widget.parse_ports_input("1-1024", "range")
# Returns: [1, 2, 3, ..., 1024]
# Max 5000 ports to prevent abuse
```

**Common Services Mode:**
```python
# Automatically uses 30 common service ports
# SSH, HTTP, HTTPS, DNS, MySQL, PostgreSQL, etc.
```

#### 2. Port Scanning

The `scan_ports()` method orchestrates the scan:

```python
1. Validate host input (not empty)
2. Parse ports based on selected mode
3. Show loading state with progress message
4. Call Phase 3's check_multiple_ports()
   - Concurrent TCP connection attempts
   - Configurable timeout (1-30 seconds)
   - Max 10 concurrent workers
5. Display results with color coding:
   - GREEN: OPEN ports
   - RED: CLOSED ports
   - YELLOW: FILTERED ports (likely firewall)
   - DIM: TIMEOUT/ERROR
6. Show summary statistics
   - Total scanned
   - Open/Closed/Filtered count
   - Average response time
```

#### 3. Results Display

Results table shows:

| Port | Service | Status | Time (ms) |
|------|---------|--------|----------|
| 22 | SSH | [green]open[/green] | 5.2 |
| 80 | HTTP | [green]open[/green] | 4.8 |
| 443 | HTTPS | [red]closed[/red] | 3.1 |

Summary line:
```
Total: 30 | [green]Open: 2[/green] | [red]Closed: 28[/red] | [yellow]Filtered: 0[/yellow] | Avg Time: 4.2ms
```

## Testing Strategy

The test suite (`test_phase4_port_scanner_widget.py`) includes 31 comprehensive tests organized into 6 categories:

### 1. Initialization Tests (3 tests)
- Widget instantiation
- Inheritance from BaseWidget
- Flag initialization (`scan_in_progress`)

### 2. UI Method Tests (6 tests)
- Compose method (UI layout)
- Button handlers (Scan, Clear)
- Select handler (Mode changes)
- Method availability

### 3. Port Parsing Tests (14 tests)
- **Single port:** valid, invalid, boundaries (1, 65535)
- **Multiple ports:** valid, spaces, duplicates, invalid format
- **Port ranges:** valid, spaces, reversed order, too large
- **Edge cases:** empty input, invalid format

### 4. Foundation Feature Tests (5 tests)
- BaseWidget inheritance
- Error handling capabilities
- Caching mechanisms
- Progress tracking
- Status management

### 5. Integration Tests (2 tests)
- PortStatus enum availability
- PortCheckResult dataclass structure
- COMMON_SERVICE_PORTS dictionary

### 6. Documentation Tests (1 test)
- All methods have docstrings

## Key Design Decisions

### 1. Reuse Existing Phase 3 Utilities

Don't reinvent:
```python
from shared.port_utils import (
    check_multiple_ports,      # Concurrent scanning
    PortStatus,                # Enum for port states
    COMMON_SERVICE_PORTS,      # 30+ service mappings
    summarize_port_scan,       # Summary statistics
)
```

### 2. Concurrent Scanning

Default to 10 concurrent workers:
```python
results = check_multiple_ports(
    host="localhost",
    ports=[22, 80, 443, ...],
    timeout=3,
    max_workers=10  # Non-blocking concurrent scans
)
```

### 3. Input Validation

Strict validation prevents abuse:
- Port range: 1-65535
- Max range size: 5000 ports (prevents DoS)
- Timeout: 1-30 seconds
- Host: non-empty, basic validation

### 4. Color Coding for Status

Quick visual feedback:
- **Green** = OPEN (what users care about)
- **Red** = CLOSED (expected, safe to ignore)
- **Yellow** = FILTERED (firewall/IDS likely)
- **Dim** = TIMEOUT/ERROR (network issues)

### 5. Non-Blocking Scanning

UI never freezes:
- Uses BaseWidget's progress tracking
- Shows loading message during scan
- Can potentially add worker thread support later

## Usage Example

### Scanning Common Ports

1. Widget loads with default "Common Services" mode
2. User enters hostname: "192.168.1.1"
3. Clicks "Scan"
4. Widget scans all 30 common service ports
5. Results show which are open/closed

### Scanning Specific Port Range

1. User selects "Port Range" mode
2. Enters "1-1024"
3. Sets timeout to 2 seconds (faster scanning)
4. Clicks "Scan"
5. Scans 1024 ports concurrently
6. Results show open ports and response times

### Scanning Multiple Specific Ports

1. User selects "Multiple Ports" mode
2. Enters "22,80,443,3306,5432"
3. Clicks "Scan"
4. Quickly identifies which services are running

## Testing Commands

```bash
# Run all Port Scanner tests
pytest tests/test_phase4_port_scanner_widget.py -v

# Run specific test category
pytest tests/test_phase4_port_scanner_widget.py::TestPortParsingLogic -v

# Run with coverage
pytest tests/test_phase4_port_scanner_widget.py --cov=src.tui.widgets.port_scanner_widget

# Run all Phase 4 tests
pytest tests/test_phase4*.py -v
```

## Success Criteria

Phase 4.3 is complete when:

✅ Port Scanner Widget implemented (13KB)  
✅ All 31 tests passing (100%)  
✅ Port parsing robust (handles all edge cases)  
✅ Concurrent scanning functional  
✅ Results display clear and color-coded  
✅ Error handling matches Phase 4.2 quality  
✅ Documentation complete  
✅ Code follows project style guide  

## Performance Metrics

**Expected Test Execution:**
- 31 tests
- ~0.5-1.0 seconds total runtime
- 100% pass rate (no mocking of real network operations)

**Scanning Performance (at runtime):**
- 30 common ports: ~10-15 seconds (depends on timeout, concurrent responses)
- 5 specific ports: ~5-10 seconds
- 1024 port range: ~60-120 seconds (with 2s timeout)

## Phase 4.3 Checklist

### Implementation
- [x] Create port_scanner_widget.py
- [x] Implement PortScannerWidget class
- [x] Implement parse_ports_input() with 4 modes
- [x] Implement scan_ports() with Phase 3 integration
- [x] Implement clear_results() UI cleanup
- [x] Add error handling and validation
- [x] Add color-coded status display
- [x] Add summary statistics

### Testing
- [x] Create test_phase4_port_scanner_widget.py
- [x] Write 31 comprehensive tests
- [x] Test initialization
- [x] Test UI methods
- [x] Test port parsing (all modes)
- [x] Test foundation features
- [x] Test Phase 3 integration
- [x] Test edge cases

### Integration
- [x] Add PortScannerWidget to widgets/__init__.py
- [x] Update package exports
- [x] Create documentation
- [x] Add usage examples

### Next Steps (Phase 4.4)
- [ ] Integrate Port Scanner into main TUI app
- [ ] Add keyboard shortcut (maybe 'P'?)
- [ ] Add history/caching of scan results
- [ ] Consider export to CSV/JSON

## Related Documentation

- [Phase 3 Diagnostics API](./phase3-diagnostics-api.md) - Port utilities reference
- [Phase 4.1 Foundation](./phase4-integration.md) - BaseWidget and AsyncOperationMixin
- [Phase 4.2 DNS Widget](./phase4.2-dns-widget.md) - Reference implementation
- [Main README](../README.md) - Project overview

## Questions/Issues

If tests fail or implementation issues arise:

1. Check Phase 4.2 DNS Widget for reference patterns
2. Review Phase 3 port_utils.py for API details
3. Check BaseWidget documentation for error handling patterns
4. See test_phase4_port_scanner_widget.py for expected behavior
