# Phase 4: TUI Integration Roadmap

**Target Version:** v0.4.0  
**Status:** Planning Phase  
**Expected Release:** Q1 2026

## Overview

Phase 4 will integrate the Phase 3 advanced diagnostics (DNS, port scanning, latency analysis) into the Textual-based Terminal User Interface (TUI), creating a seamless user experience for network professionals. This phase focuses on making the powerful diagnostic utilities accessible through interactive widgets with real-time updates and visual feedback.

## Goals

### Primary Objectives
- Integrate all Phase 3 diagnostic utilities into the TUI
- Provide interactive widgets with real-time progress tracking
- Enable result history and comparison capabilities
- Support export functionality for diagnostic results
- Maintain performance and responsiveness during long-running operations

### User Experience Goals
- Zero learning curve for existing TUI users
- Keyboard-first navigation with mouse support
- Non-blocking operations with cancellation support
- Clear visual feedback during diagnostics
- Intuitive result presentation and filtering

## Architecture

### Widget Framework

```
src/tui/widgets/
├── dns_resolver_widget.py      # DNS lookup and propagation checking
├── port_scanner_widget.py      # Interactive port scanning
├── latency_analyzer_widget.py  # Ping and traceroute visualization
├── results_history_widget.py   # Historical results viewer
└── export_widget.py            # Result export functionality
```

### Integration Points

```python
# Current TUI structure
src/tui/
├── app.py                      # Main Textual application
├── tabs/
│   ├── dashboard.py            # System overview
│   ├── speed_test.py           # Speed testing
│   ├── ping_tool.py            # Continuous ping
│   ├── connection_details.py  # Interface info
│   ├── nmap_scanner.py         # Network scanning
│   └── utilities.py            # NEW: Advanced Diagnostics Hub
└── widgets/                    # NEW: Phase 4 widgets

# Phase 3 utilities (already complete)
src/shared/
├── dns_utils.py
├── port_utils.py
└── latency_utils.py
```

## Feature Breakdown

### 1. DNS Resolver Widget

**Location:** New tab in Utilities section or standalone "DNS" tab

#### Features
- **Hostname Lookup**
  - Input field for hostname/domain
  - Real-time validation of input
  - Display IPv4/IPv6 addresses with copy-to-clipboard
  - Show reverse DNS (PTR) records
  - Display lookup time and status

- **DNS Server Validation**
  - Test custom DNS servers (8.8.8.8, 1.1.1.1, etc.)
  - Response time measurement
  - Health status indicator (responsive/timeout/error)

- **Propagation Checker**
  - Query 5 major DNS providers simultaneously
  - Side-by-side comparison table
  - Highlight inconsistencies across providers
  - Automatic refresh capability

#### UI Mockup
```
┌─ DNS Resolver ────────────────────────────────────────────┐
│ Hostname: [example.com________________] [Resolve]         │
│                                                            │
│ ● IPv4 Addresses:                                          │
│   93.184.216.34  [Copy]                                    │
│                                                            │
│ ● IPv6 Addresses:                                          │
│   2606:2800:220:1:248:1893:25c8:1946  [Copy]              │
│                                                            │
│ ● Reverse DNS: example.com                                 │
│ ● Lookup Time: 23.45ms                                     │
│                                                            │
│ [Check Propagation] [Validate DNS Server]                 │
└────────────────────────────────────────────────────────────┘
```

#### Technical Implementation
```python
from textual.app import ComposeResult
from textual.widgets import Input, Button, Static, DataTable
from textual.containers import Container
from src.shared.dns_utils import resolve_hostname, check_dns_propagation

class DNSResolverWidget(Container):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter hostname...", id="hostname-input")
        yield Button("Resolve", variant="primary", id="resolve-btn")
        yield Static(id="dns-results")
        yield DataTable(id="propagation-table")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "resolve-btn":
            hostname = self.query_one("#hostname-input", Input).value
            # Run in worker to avoid blocking UI
            self.run_worker(self.resolve_dns(hostname))
    
    async def resolve_dns(self, hostname: str) -> None:
        result = await self.run_in_thread(resolve_hostname, hostname)
        self.update_results(result)
```

### 2. Port Scanner Widget

**Location:** New tab "Port Scanner" or within Utilities

#### Features
- **Single Port Check**
  - Quick connectivity test
  - Display service name and status
  - Show response time
  - Optional banner grabbing

- **Multi-Port Scan**
  - Select from presets (Web, Database, Mail, All Common)
  - Custom port range (e.g., 1-1024, 8000-9000)
  - CSV import for custom port lists
  - Concurrent scanning with progress bar

- **Results Display**
  - Sortable table (port, service, status, time)
  - Color-coded status (green=open, red=closed, yellow=filtered)
  - Filter by status (show only open ports)
  - Export results to JSON/CSV

#### UI Mockup
```
┌─ Port Scanner ────────────────────────────────────────────┐
│ Target: [192.168.1.1__________] Preset: [Common Ports ▼] │
│                                                            │
│ ○ Single Port  ● Port Range  ○ Custom List                │
│ Ports: [1____] to [1024_]  Workers: [10__]                │
│                                                            │
│ [Start Scan]  [Stop]  [Export]     Progress: ████░░ 67%   │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐│
│ │Port │ Service    │ Status   │ Time     │ Banner       ││
│ ├─────┼────────────┼──────────┼──────────┼──────────────┤│
│ │  22 │ SSH        │ ● OPEN   │   12ms   │ SSH-2.0-Open ││
│ │  80 │ HTTP       │ ○ CLOSED │    8ms   │ -            ││
│ │ 443 │ HTTPS      │ ● OPEN   │   15ms   │ -            ││
│ │3306 │ MySQL      │ ⚠ FILTER │ 5000ms   │ -            ││
│ └─────┴────────────┴──────────┴──────────┴──────────────┘│
│                                                            │
│ Open: 12 | Closed: 145 | Filtered: 3 | Total: 160         │
└────────────────────────────────────────────────────────────┘
```

#### Technical Implementation
```python
from textual.widgets import DataTable, ProgressBar, Select
from textual.worker import Worker
from src.shared.port_utils import check_multiple_ports, scan_common_ports

class PortScannerWidget(Container):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Target IP/hostname", id="target-input")
        yield Select(
            options=[("Common Ports", "common"), ("Web Services", "web"), ("Databases", "db")],
            id="preset-select"
        )
        yield ProgressBar(id="scan-progress")
        yield DataTable(id="port-results")
        yield Static(id="scan-summary")
    
    async def start_scan(self, target: str, ports: list[int]) -> None:
        # Use worker with progress callback
        worker = self.run_worker(
            self.scan_ports(target, ports),
            name="port-scan",
            group="scanning"
        )
        
    async def scan_ports(self, target: str, ports: list[int]) -> None:
        results = await self.run_in_thread(check_multiple_ports, target, ports)
        self.update_table(results)
```

### 3. Latency Analyzer Widget

**Location:** Enhanced "Ping Tool" tab or new "Latency Analysis" tab

#### Features
- **Enhanced Ping Statistics**
  - Real-time ping with live graph
  - Min/avg/max/jitter display
  - Packet loss percentage
  - Quality rating (Excellent/Good/Poor)
  - Historical data retention (last 100 pings)

- **Visual Latency Graph**
  - Line chart showing RTT over time
  - Jitter visualization
  - Packet loss indicators
  - Configurable time window (1min, 5min, 1hr)

- **Traceroute Visualization**
  - MTR-style hop-by-hop display
  - Per-hop latency bars
  - Geographic location hints (if available)
  - Export path analysis

#### UI Mockup
```
┌─ Latency Analyzer ────────────────────────────────────────┐
│ Target: [8.8.8.8__________]  Count: [10__]  [Start Ping]  │
│                                                            │
│ ┌─ Live Statistics ──────────────────────────────────────┐│
│ │ Min: 12.34ms  Avg: 15.67ms  Max: 18.90ms  Jitter: 1.8ms││
│ │ Packets: 10 sent, 10 received, 0% loss                 ││
│ │ Quality: ✅ Excellent (stable latency)                  ││
│ └────────────────────────────────────────────────────────┘│
│                                                            │
│ ┌─ Latency Graph ────────────────────────────────────────┐│
│ │ 20ms│     ●                        ●                   ││
│ │ 15ms│  ●    ●  ●  ●     ●    ●  ●    ●  ●             ││
│ │ 10ms│                                                  ││
│ │  5ms│                                                  ││
│ │  0ms└─────────────────────────────────────────────────┘│
│ └────────────────────────────────────────────────────────┘│
│                                                            │
│ [Run Traceroute]  [Export Data]  [Clear History]          │
└────────────────────────────────────────────────────────────┘
```

#### Technical Implementation
```python
from textual_plotext import PlotextPlot
from src.shared.latency_utils import ping_statistics, mtr_style_trace

class LatencyAnalyzerWidget(Container):
    ping_history: list[float] = []
    
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Target IP/hostname", id="target-input")
        yield Static(id="stats-display")
        yield PlotextPlot(id="latency-graph")
        yield Button("Start Continuous Ping", id="ping-btn")
        yield Button("Run Traceroute", id="trace-btn")
    
    async def continuous_ping(self, target: str) -> None:
        while self.is_running:
            stats = await self.run_in_thread(ping_statistics, target, count=1)
            if stats.individual_rtts:
                self.ping_history.append(stats.individual_rtts[0])
                self.update_graph()
            await asyncio.sleep(1)
```

### 4. Results History & Export

#### Features
- **Persistent Storage**
  - Save all diagnostic results to SQLite database
  - Searchable history by target/date/type
  - Comparison of historical results
  - Automatic cleanup of old results (configurable retention)

- **Export Formats**
  - JSON (machine-readable)
  - CSV (spreadsheet compatible)
  - HTML (formatted reports)
  - Markdown (documentation)
  - PDF (requires external library)

- **Result Management**
  - Tag/label important results
  - Add notes/comments to results
  - Share results via export
  - Delete individual or bulk results

## Implementation Plan

### Phase 4.1: Foundation (Weeks 1-2)
- [ ] Create widget base classes
- [ ] Implement worker patterns for non-blocking operations
- [ ] Set up progress tracking infrastructure
- [ ] Design consistent UI components

### Phase 4.2: DNS Integration (Weeks 3-4)
- [ ] Build DNS Resolver widget
- [ ] Implement propagation checker UI
- [ ] Add DNS server validation interface
- [ ] Write integration tests

### Phase 4.3: Port Scanner Integration (Weeks 5-6)
- [ ] Build Port Scanner widget
- [ ] Implement preset configurations
- [ ] Add progress tracking and cancellation
- [ ] Create results table with filtering

### Phase 4.4: Latency Integration (Weeks 7-8)
- [ ] Enhance existing Ping Tool
- [ ] Add visual latency graphing
- [ ] Implement traceroute visualization
- [ ] Add real-time updates

### Phase 4.5: History & Export (Weeks 9-10)
- [ ] Implement SQLite storage backend
- [ ] Build results history viewer
- [ ] Create export functionality (JSON, CSV, HTML)
- [ ] Add result comparison features

### Phase 4.6: Testing & Documentation (Weeks 11-12)
- [ ] Write comprehensive TUI tests
- [ ] Create user documentation
- [ ] Record demo videos
- [ ] Performance optimization
- [ ] Release v0.4.0

## Technical Considerations

### Performance
- Use Textual workers for all long-running operations
- Implement cancellation support for all diagnostics
- Add progress callbacks for user feedback
- Limit concurrent operations to prevent resource exhaustion

### User Experience
- Provide keyboard shortcuts for all actions
- Support tab navigation between fields
- Add context-sensitive help (F1)
- Implement undo/redo where applicable

### Error Handling
- Display user-friendly error messages
- Provide actionable recovery suggestions
- Log errors for debugging
- Gracefully degrade on missing tools (MTR, Nmap)

### Data Management
- Store results in `~/.network-triage/results.db`
- Implement automatic database migrations
- Add data export/import for portability
- Respect user privacy (no telemetry)

## Testing Strategy

### Unit Tests
- Widget rendering and layout
- Event handling and user input
- Worker execution and cancellation
- Data persistence and retrieval

### Integration Tests
- End-to-end diagnostic workflows
- Cross-widget communication
- Error scenarios and recovery
- Performance under load

### Manual Testing
- Usability testing with network professionals
- Cross-platform validation (Windows, Linux, macOS)
- Accessibility testing (keyboard-only navigation)
- Performance profiling

## Success Metrics

### Functional Goals
- All Phase 3 utilities accessible via TUI
- <100ms UI response time during operations
- <5% test failure rate across platforms
- 100% feature parity with CLI utilities

### User Experience Goals
- <30 seconds time-to-first-result for new users
- <3 clicks/keystrokes for common operations
- >90% user satisfaction in usability testing
- Zero data loss during normal operations

## Dependencies

### Required
- Textual >= 0.75.0 (current TUI framework)
- Python 3.11+ (async support)
- SQLite3 (built into Python)

### Optional
- textual-plotext (for latency graphs)
- rich-pixels (for advanced visualizations)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance degradation during scans | High | Use workers, implement cancellation, limit concurrency |
| Complex UI overwhelming users | Medium | Progressive disclosure, presets, contextual help |
| Cross-platform compatibility issues | Medium | Extensive CI/CD testing, platform-specific code paths |
| Database corruption | Low | Regular backups, transaction safety, schema versioning |

## Future Enhancements (Phase 5+)

### Advanced Analytics
- Trend analysis over time
- Anomaly detection
- Performance baselines
- Network health scoring

### Visualization
- Network topology mapping
- Geographic traceroute visualization
- Custom dashboards
- Real-time alerting

### Integration
- Cloud platform APIs (AWS, Azure, GCP)
- Network device management (SNMP)
- Ticketing systems (Jira, ServiceNow)
- Monitoring platforms (Prometheus, Grafana)

### Automation
- Scheduled diagnostics
- Automated reporting
- Custom scripts and plugins
- API for external tools

## Documentation

Phase 4 will include:
- Updated README with TUI screenshots
- Widget API reference
- User guide with tutorials
- Video walkthroughs
- Migration guide from CLI

## Community Feedback

We're seeking input on:
1. Most critical features for first release
2. UI/UX preferences and pain points
3. Export format priorities
4. Integration with existing workflows

**Share feedback:** https://github.com/knowoneactual/Network-Triage-Tool/discussions

## Timeline

```
Q1 2026
├─ January: Foundation + DNS Integration (4.1, 4.2)
├─ February: Port Scanner + Latency (4.3, 4.4)
└─ March: History/Export + Testing (4.5, 4.6)
    └─ v0.4.0 Release
```

## Conclusion

Phase 4 will transform the Network Triage Tool from a powerful CLI utility into a comprehensive TUI application, making advanced diagnostics accessible to network professionals of all skill levels. By focusing on usability, performance, and reliability, we'll deliver a production-ready tool that enhances productivity and simplifies network troubleshooting.

---

**Questions or suggestions?** Open an issue or discussion on GitHub!

**Current Status:** Phase 3 Complete ✅ | Phase 4 Planning 📋
