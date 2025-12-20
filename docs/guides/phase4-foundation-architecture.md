# Phase 4.1: Widget Foundation Architecture

**Status:** 🚀 In Development  
**Target:** v0.4.0  
**Timeline:** Weeks 1-2 of Phase 4  

---

## Overview

Phase 4.1 establishes the foundational architecture for all Phase 4 widgets. This includes:

- **BaseWidget**: Foundation class for all widgets with error handling, progress tracking, and worker integration
- **AsyncOperationMixin**: Patterns for non-blocking operations
- **Reusable Components**: ResultsWidget, ProgressWidget, StatusIndicator, ErrorDisplay, SummaryWidget
- **WidgetTemplate**: Copy-paste template for creating new widgets

---

## Core Concepts

### 1. BaseWidget Class

All Phase 4 widgets inherit from `BaseWidget`, which provides:

```python
from src.tui.widgets.base import BaseWidget
from textual.app import ComposeResult
from textual.widgets import Input, Button

class DNSResolverWidget(BaseWidget):
    def compose(self) -> ComposeResult:
        yield Input(id="hostname-input", placeholder="example.com")
        yield Button("Resolve", id="resolve-btn")
    
    async def on_button_pressed(self, event):
        if event.button.id == "resolve-btn":
            hostname = self.query_one("#hostname-input").value
            self.show_loading("Resolving...")
            # Async operation happens here
```

#### BaseWidget Features

| Feature | Purpose | Example |
|---------|---------|----------|
| **Error Handling** | Consistent error display | `self.display_error("Connection failed")` |
| **Progress Tracking** | Show operation status | `self.show_loading("Processing...")` |
| **Worker Integration** | Non-blocking operations | Built-in via `AsyncOperationMixin` |
| **Result Caching** | Cache operation results | `self.cache_result(key, value)` |
| **Status Management** | Track widget state | `self.set_status("Ready")` |

#### Reactive Attributes

```python
class BaseWidget:
    is_loading = reactive(False)      # True when operation running
    current_status = reactive("Ready") # Current status message
    error_message = reactive("")      # Current error message
```

### 2. AsyncOperationMixin

Provides patterns for executing operations without freezing the UI:

```python
from src.tui.widgets.base import AsyncOperationMixin, OperationResult

class MyWidget(BaseWidget, AsyncOperationMixin):
    async def long_operation(self) -> OperationResult[str]:
        try:
            self.show_loading("Processing...")
            
            # Run in thread to avoid blocking UI
            result = await self.run_in_thread(expensive_function)
            
            return OperationResult(success=True, data=result)
        
        except Exception as e:
            return self.handle_error(e, "Operation failed")
```

#### Key Methods

```python
# Caching
self.cache_result(key="dns_lookup_google.com", result=ip_list)
result = self.get_cached("dns_lookup_google.com")
self.clear_cache(key="specific_key")  # or clear all
self.enable_cache(False)  # disable temporarily

# Error Handling
result = self.handle_error(exception, custom_message="Custom error")

# Operation Cancellation
self.cancel_operations()  # Cancel all workers
self.cancel_operations("worker_name")  # Cancel specific worker
```

### 3. OperationResult Dataclass

Standardized result object for all async operations:

```python
from src.tui.widgets.base import OperationResult

# Success result
result = OperationResult(
    success=True,
    data="operation_result",
    duration_ms=123.45
)

# Error result
result = OperationResult(
    success=False,
    error="DNS resolution failed",
    error_type=socket.timeout,
    duration_ms=5000.0
)
```

---

## Reusable Components

### ResultsWidget

Standardized table for displaying operation results:

```python
from src.tui.widgets.components import ResultsWidget, ResultColumn

class PortScannerWidget(BaseWidget):
    def compose(self) -> ComposeResult:
        columns = [
            ResultColumn("Port", "port", cell_width=10),
            ResultColumn("Service", "service", cell_width=15),
            ResultColumn("Status", "status", cell_width=12),
            ResultColumn("Time", "time", cell_width=10),
        ]
        self.results = ResultsWidget(columns=columns)
        yield self.results
    
    def add_result(self, port: int, service: str, status: str, time: str):
        self.results.add_row(
            port=port,
            service=service,
            status=status,
            time=time
        )
    
    def get_all_results(self):
        return self.results.get_results()
```

### ProgressWidget

Standardized progress display:

```python
from src.tui.widgets.components import ProgressWidget

class MyWidget(BaseWidget):
    def compose(self) -> ComposeResult:
        self.progress = ProgressWidget()
        yield self.progress
    
    async def long_operation(self):
        total = 100
        for i in range(total):
            self.progress.update(i, total, f"Processing {i}/{total}")
            await asyncio.sleep(0.1)
        self.progress.update(total, total, "Complete!")
```

### StatusIndicator

Color-coded status display:

```python
from src.tui.widgets.components import StatusIndicator

class MyWidget(BaseWidget):
    def compose(self) -> ComposeResult:
        self.status = StatusIndicator(status="pending", text="Waiting...")
        yield self.status
    
    async def operation(self):
        self.status.set_status("pending", "Running operation...")
        # Do work
        self.status.set_status("success", "Operation complete!")
```

### ErrorDisplay

Consistent error message display:

```python
from src.tui.widgets.components import ErrorDisplay

class MyWidget(BaseWidget):
    def compose(self) -> ComposeResult:
        self.error_display = ErrorDisplay()
        yield self.error_display
    
    async def operation(self):
        try:
            # Do work
            pass
        except Exception as e:
            self.error_display.show_error(
                message="Operation failed",
                details=str(e)
            )
```

### SummaryWidget

Key-value statistics display:

```python
from src.tui.widgets.components import SummaryWidget

class PortScannerWidget(BaseWidget):
    def compose(self) -> ComposeResult:
        self.summary = SummaryWidget()
        yield self.summary
    
    def display_results(self, results):
        open_ports = len([r for r in results if r['status'] == 'OPEN'])
        closed_ports = len([r for r in results if r['status'] == 'CLOSED'])
        
        self.summary.add_stat("Open", str(open_ports), color="green")
        self.summary.add_stat("Closed", str(closed_ports), color="red")
        self.summary.add_stat("Total", str(len(results)))
```

---

## Widget Template

Use `WidgetTemplate` as a starting point for new widgets:

```python
from src.tui.widgets.base import WidgetTemplate, OperationResult
from textual.app import ComposeResult
from textual.widgets import Input, Button, DataTable
from src.tui.widgets.components import ResultsWidget, ResultColumn

class DNSResolverWidget(WidgetTemplate):
    """DNS Resolver Widget - Template example."""
    
    def __init__(self):
        super().__init__(name="DNSResolver")
    
    def compose(self) -> ComposeResult:
        yield Input(id="hostname-input", placeholder="example.com")
        yield Button("Resolve", id="resolve-btn")
        yield ResultsWidget(
            columns=[
                ResultColumn("Type", "type", cell_width=10),
                ResultColumn("Address", "address", cell_width=30),
            ],
            id="results-table"
        )
    
    async def on_button_pressed(self, event):
        if event.button.id == "resolve-btn":
            hostname = self.query_one("#hostname-input").value
            await self.resolve_hostname(hostname)
    
    async def resolve_hostname(self, hostname: str) -> None:
        try:
            self.show_loading(f"Resolving {hostname}...")
            
            # Import Phase 3 utilities
            from src.shared.dns_utils import resolve_hostname
            
            result = await self.run_in_thread(resolve_hostname, hostname)
            
            # Display results
            results_table = self.query_one("#results-table", ResultsWidget)
            for ipv4 in result.ipv4_addresses:
                results_table.add_row(type="A", address=ipv4)
            for ipv6 in result.ipv6_addresses:
                results_table.add_row(type="AAAA", address=ipv6)
            
            self.display_success(f"Resolved {hostname}")
        
        except Exception as e:
            self.display_error(str(e))
```

---

## Error Handling Patterns

### Pattern 1: Try-Except with User Feedback

```python
async def operation(self):
    try:
        self.show_loading("Executing operation...")
        result = await self.run_in_thread(expensive_function)
        self.display_success("Operation complete")
        return result
    except TimeoutError as e:
        self.display_error("Operation timed out")
    except ConnectionError as e:
        self.display_error(f"Connection failed: {str(e)}")
    except Exception as e:
        self.display_error(f"Unexpected error: {str(e)}")
```

### Pattern 2: Using OperationResult

```python
async def operation(self) -> OperationResult[dict]:
    try:
        self.show_loading("Processing...")
        result = await self.run_in_thread(expensive_function)
        return OperationResult(success=True, data=result)
    except Exception as e:
        return self.handle_error(e, "Operation failed")
```

### Pattern 3: With Result Caching

```python
async def operation(self, key: str) -> OperationResult[dict]:
    # Check cache first
    cached = self.get_cached(key)
    if cached:
        return OperationResult(success=True, data=cached)
    
    try:
        self.show_loading("Executing...")
        result = await self.run_in_thread(expensive_function, key)
        self.cache_result(key, result)  # Cache for future use
        return OperationResult(success=True, data=result)
    except Exception as e:
        return self.handle_error(e)
```

---

## Testing Patterns

### Unit Testing BaseWidget

```python
import pytest
from src.tui.widgets.base import BaseWidget, OperationResult

def test_base_widget_error_display():
    """Test error display."""
    widget = BaseWidget()
    widget.display_error("Test error")
    
    assert widget.error_message == "Test error"
    assert widget.current_status == "Error"

def test_base_widget_loading_state():
    """Test loading state."""
    widget = BaseWidget()
    widget.show_loading("Processing...")
    
    assert widget.is_loading is True
    assert widget.current_status == "Processing..."

def test_operation_result():
    """Test OperationResult."""
    result = OperationResult(success=True, data="test_data", duration_ms=100)
    
    assert result.success is True
    assert result.data == "test_data"
    assert result.duration_ms == 100
    assert result.timestamp is not None
```

### Unit Testing Custom Widget

```python
def test_dns_resolver_widget():
    """Test DNS Resolver widget."""
    widget = DNSResolverWidget()
    
    # Test initialization
    assert widget.widget_name == "DNSResolver"
    assert widget.is_loading is False
    
    # Test cache functionality
    widget.cache_result("example.com", ["93.184.216.34"])
    cached = widget.get_cached("example.com")
    assert cached == ["93.184.216.34"]
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Phase 4.1 Foundation                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │ AsyncOperationMixin (patterns for async ops)    │   │
│  ├──────────────────────────────────────────────────┤   │
│  │ - cache_result(), get_cached(), clear_cache()   │   │
│  │ - cancel_operations()                            │   │
│  │ - handle_error()                                 │   │
│  └──────────────────────────────────────────────────┘   │
│                         △                                │
│                         │ inherits                        │
│  ┌──────────────────────┴──────────────────────────┐   │
│  │      BaseWidget (foundation for all widgets)    │   │
│  ├───────────────────────────────────────────────────┤  │
│  │ Reactive: is_loading, current_status,           │  │
│  │           error_message                         │  │
│  │                                                   │  │
│  │ Methods: display_error(), show_loading(),       │  │
│  │          set_status(), display_success()        │  │
│  └───────────────────────────────────────────────────┘  │
│                         △                                │
│     ┌─────────────────┬─┴────────────────┬──────────┐   │
│     │                 │                  │          │   │
│  Phase 4.2         Phase 4.3          Phase 4.4  Phase  │
│  DNS Resolver    Port Scanner      Latency       4.5   │
│  Widget          Widget            Analyzer      History│
│                                    Widget        Widget │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │            Reusable Components                    │   │
│  ├──────────────────────────────────────────────────┤   │
│  │ • ResultsWidget (sortable table)                 │   │
│  │ • ProgressWidget (progress bar with stats)      │   │
│  │ • StatusIndicator (health/status display)       │   │
│  │ • ErrorDisplay (error message display)          │   │
│  │ • SummaryWidget (key-value statistics)          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist

### Foundation Code
- [x] `BaseWidget` class implementation
- [x] `AsyncOperationMixin` class implementation
- [x] `OperationResult` dataclass
- [x] `WidgetTemplate` template class
- [x] `ResultsWidget` component
- [x] `ProgressWidget` component
- [x] `StatusIndicator` component
- [x] `ErrorDisplay` component
- [x] `SummaryWidget` component

### Testing
- [x] Unit tests for BaseWidget
- [x] Unit tests for AsyncOperationMixin
- [x] Unit tests for OperationResult
- [x] Unit tests for all components
- [x] Error handling pattern tests
- [ ] Integration tests with TUI app
- [ ] Performance benchmarks

### Documentation
- [x] Architecture guide (this file)
- [ ] API reference
- [ ] Code examples for each component
- [ ] Best practices guide
- [ ] Troubleshooting guide

### Quality Assurance
- [x] Code review
- [ ] Cross-platform testing (Win/Linux/Mac)
- [ ] Performance profiling
- [ ] Accessibility testing

---

## Next Steps

Once Phase 4.1 Foundation is complete:

1. **Week 3-4:** Implement [Phase 4.2: DNS Resolver Widget](./dns-resolver.md)
2. **Week 5-6:** Implement [Phase 4.3: Port Scanner Widget](./port-scanner.md)
3. **Week 7-9:** Implement [Phase 4.4: Latency Analyzer Widget](./latency-analyzer.md)
4. **Week 9-10:** Implement [Phase 4.5: Results History & Export](./results-management.md)
5. **Week 11-12:** Testing, documentation, release v0.4.0

---

## References

- [Textual Documentation](https://textual.textualize.io/)
- [Textual Widgets Guide](https://textual.textualize.io/guide/widgets/)
- [Phase 3 Diagnostics API](./phase3-diagnostics-api.md)
- [Error Handling Guide](./error-handling.md)

