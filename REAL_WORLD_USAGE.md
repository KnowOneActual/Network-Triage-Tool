# Phase 4.3 - Real World TUI Usage Guide

## How the Port Scanner Widget Works in Practice

This document walks through actual user interactions with the Port Scanner Widget in the TUI app.

---

## TUI User Interface Layout

When the Port Scanner Widget is displayed in the app, it looks like this:

```
┌────────────────────────────────────────────────────────────────┐
│                       Port Scanner                             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ Target Host:                                                   │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ localhost or 192.168.1.1                                 │  │  ← User enters host
│ └──────────────────────────────────────────────────────────┘  │
│                                                                │
│ Scan Mode:                                                     │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ > Common Services (30 ports)                             │  │  ← User selects mode
│ │   Single Port                                            │  │
│ │   Multiple Ports (comma-separated)                       │  │
│ │   Port Range (e.g. 1-1024)                               │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                │
│ Ports (for single/multiple/range):                            │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ e.g. 80 or 80,443,22 or 1-1024                          │  │  ← User enters ports
│ └──────────────────────────────────────────────────────────┘  │
│                                                                │
│ Timeout per port (seconds):                                   │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ 3                                                        │  │  ← User sets timeout
│ └──────────────────────────────────────────────────────────┘  │
│                                                                │
│ ┌─────────────┐  ┌────────┐                                   │
│ │   Scan      │  │ Clear  │                                   │  ← Action buttons
│ └─────────────┘  ┌────────┐                                   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                          Results                              │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ Port | Service           | Status     | Time (ms)             │
│ ──── | ──────────────── | ────────── | ──────────           │
│  22  │ SSH              │ ✓ OPEN     │ 5.2                   │
│  80  │ HTTP             │ ✓ OPEN     │ 4.8                   │
│ 443  │ HTTPS            │ ✗ CLOSED   │ 3001.0                │
│3306  │ MySQL            │ ⚠ FILTERED │ 3003.0                │
│                                                                │
│ Total: 30 | Open: 2 | Closed: 27 | Filtered: 1 | Avg: 8.2ms │
│                                                                │
│ Status: ✓ Scanned 192.168.1.1 - 2 open, 27 closed, 1 filtered│
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Real World Scenario 1: Scan Common Ports on a Host

### User Steps:

**1. Enter Target Host**
```
User types: "192.168.1.1"
```

**2. Select Scan Mode** (Default: "Common Services")
```
Already selected - no change needed
Mode: Common Services (30 ports)
```

**3. Leave Port Input Empty** (Not needed for common scan)
```
Port input is ignored when mode is "common"
```

**4. Keep Default Timeout** (3 seconds)
```
Default value: 3 seconds (perfect for LAN)
```

**5. Click "Scan" Button**
```
UserKey: S or click the button
```

### Execution Flow:

```python
1. scan_ports() is called
   ↓
2. Gets inputs:
   - host = "192.168.1.1"
   - scan_mode = "common"
   - timeout = 3 seconds
   ↓
3. Mode is "common" so:
   ports_to_scan = [22, 80, 443, 3306, 5432, ...] (30 common ports)
   ↓
4. Show loading: "Scanning 192.168.1.1 (common services - 30 ports)..."
   set_status("Scanning 192.168.1.1...")
   ↓
5. Call Phase 3 utility:
   results = check_multiple_ports(
       "192.168.1.1",
       [22, 80, 443, ...],
       timeout=3,
       max_workers=10  # Concurrent scanning
   )
   ↓
6. Results come back with status for each port:
   Port 22:   OPEN   (SSH response in 5.2ms)
   Port 80:   OPEN   (HTTP response in 4.8ms)
   Port 443:  CLOSED (Connection refused in 3001ms)
   Port 3306: FILTERED (No response in 3003ms)
   ...
   ↓
7. Display results in table:
   Port | Service | Status       | Time
   ──── | ─────── | ──────────── | ─────
    22  │ SSH     │ ✓ OPEN       │ 5.2
    80  │ HTTP    │ ✓ OPEN       │ 4.8
   443  │ HTTPS   │ ✗ CLOSED     │ 3001.0
   3306 │ MySQL   │ ⚠ FILTERED   │ 3003.0
   ...
   ↓
8. Show summary:
   "Total: 30 | Open: 2 | Closed: 27 | Filtered: 1 | Avg: 8.2ms"
   ↓
9. Show success message:
   "Scan complete! Found 2 open port(s) on 192.168.1.1"
   ↓
10. Update status bar:
    "✓ Scanned 192.168.1.1 - 2 open, 27 closed, 1 filtered"
```

### Visual Feedback:
- ✅ Loading spinner while scanning
- ✅ Color-coded results (Green=OPEN, Red=CLOSED, Yellow=FILTERED)
- ✅ Response time for each port
- ✅ Summary statistics
- ✅ Success message

---

## Real World Scenario 2: Scan Specific Ports

### User Steps:

**1. Enter Target Host**
```
User types: "example.com"
```

**2. Change Scan Mode**
```
Select: "Multiple Ports (comma-separated)"
```

**3. Enter Specific Ports**
```
User types: "80, 443, 8080, 8443"
Note: Spaces are automatically handled
```

**4. Set Custom Timeout** (Website might be slow)
```
User changes to: "5"
Timeout: 5 seconds
```

**5. Click "Scan"**

### Execution Flow:

```python
1. scan_ports() is called
   ↓
2. Gets inputs:
   - host = "example.com"
   - scan_mode = "multiple"
   - port_str = "80, 443, 8080, 8443"
   - timeout = 5 seconds
   ↓
3. Mode is "multiple" so:
   parsed_ports = parse_ports_input("80, 443, 8080, 8443", "multiple")
   ↓
4. parse_ports_input() logic:
   - Split by comma: ["80", " 443", " 8080", " 8443"]
   - Strip whitespace: ["80", "443", "8080", "8443"]
   - Convert to int: [80, 443, 8080, 8443]
   - Validate each (1 <= port <= 65535): All valid ✓
   - Remove duplicates: [80, 443, 8080, 8443]
   - Sort: [80, 443, 8080, 8443]
   - Return: [80, 443, 8080, 8443]
   ↓
5. Scan begins:
   results = check_multiple_ports(
       "example.com",
       [80, 443, 8080, 8443],
       timeout=5,
       max_workers=10
   )
   ↓
6. Results:
   Port 80:   OPEN   (HTTP in 45ms)
   Port 443:  OPEN   (HTTPS in 52ms)
   Port 8080: CLOSED (Connection refused in 5000ms)
   Port 8443: CLOSED (Connection refused in 5000ms)
   ↓
7. Display results:
   Port | Service      | Status       | Time
   ──── | ──────────── | ──────────── | ──────
    80  │ HTTP         │ ✓ OPEN       │ 45.0
   443  │ HTTPS        │ ✓ OPEN       │ 52.0
   8080 │ HTTP-Alt     │ ✗ CLOSED     │ 5000.0
   8443 │ HTTPS-Alt    │ ✗ CLOSED     │ 5000.0
   ↓
8. Summary:
   "Total: 4 | Open: 2 | Closed: 2 | Filtered: 0 | Avg: 2524.5ms"
```

---

## Real World Scenario 3: Port Range Scan

### User Steps:

**1. Enter Target Host**
```
User types: "192.168.1.5"
```

**2. Change Scan Mode**
```
Select: "Port Range (e.g. 1-1024)"
```

**3. Enter Port Range**
```
User types: "1-100"
Note: This scans ports 1 through 100 (100 ports total)
```

**4. Set Timeout**
```
User leaves as: "3"
```

**5. Click "Scan"**

### Execution Flow:

```python
1. scan_ports() called
   ↓
2. Gets inputs:
   - host = "192.168.1.5"
   - scan_mode = "range"
   - port_str = "1-100"
   - timeout = 3 seconds
   ↓
3. Mode is "range" so:
   parsed_ports = parse_ports_input("1-100", "range")
   ↓
4. parse_ports_input() logic:
   - Check format with regex: ✓ Matches "^(\d+)\s*-\s*(\d+)$"
   - Extract start/end: start=1, end=100
   - Validate range: 1 <= 1 <= 65535 ✓, 1 <= 100 <= 65535 ✓
   - start < end? 1 < 100 ✓ (no reversal needed)
   - port_count = 100 - 1 + 1 = 100
   - Check limit: 100 <= 5000 ✓ (within limits)
   - Return: [1, 2, 3, ..., 100]
   ↓
5. Scan begins with 100 ports
   ↓
6. Results show which ports respond:
   Port 1:   CLOSED
   Port 2:   CLOSED
   ...
   Port 22:  OPEN   (SSH)
   ...
   Port 53:  OPEN   (DNS)
   ...
   Port 100: CLOSED
   ↓
7. Summary shows findings
```

---

## Error Handling in Real World

### Scenario A: Invalid Host

**User Action:**
```
1. Leave host field empty
2. Click "Scan"
```

**What Happens:**
```python
if not host:
    self.display_error("Please enter a target host")
    self.set_status("Error: No host specified")
    return
```

**User Sees:**
```
❌ Error Message: "Please enter a target host"
Status Bar: "Error: No host specified"
```

---

### Scenario B: Invalid Port in "Multiple" Mode

**User Action:**
```
1. Host: "192.168.1.1"
2. Mode: "Multiple Ports"
3. Ports: "80, 443, abc, 22"
4. Click "Scan"
```

**What Happens:**
```python
parsed_ports = parse_ports_input("80, 443, abc, 22", "multiple")

# In parse_ports_input():
for port_str in "80, 443, abc, 22".split(","):
    port = int(port_str.strip())  # ValueError on "abc"
    # Catches ValueError, logs warning, returns None

if parsed_ports is None:
    self.display_error("Invalid ports: use comma-separated numbers (1-65535)")
    return
```

**User Sees:**
```
❌ Error Message: "Invalid ports: use comma-separated numbers (1-65535)"
Status Bar: "Error state"
```

---

### Scenario C: Port Range Too Large

**User Action:**
```
1. Host: "192.168.1.1"
2. Mode: "Port Range"
3. Ports: "1-10000"
4. Click "Scan"
```

**What Happens:**
```python
parsed_ports = parse_ports_input("1-10000", "range")

# In parse_ports_input():
start = 1
end = 10000
port_count = 10000 - 1 + 1 = 10000

if port_count > 5000:
    logger.warning(f"Range too large: {port_count} ports (max 5000)")
    return None

if parsed_ports is None:
    self.display_error("Invalid range: use format 'start-end' (e.g. 1-1024)")
    return
```

**User Sees:**
```
❌ Error Message: "Invalid range: use format 'start-end' (e.g. 1-1024)"
Note: User should try "1-5000" instead
Status Bar: "Ready for new scan"
```

---

### Scenario D: Invalid Timeout

**User Action:**
```
1. Host: "192.168.1.1"
2. Mode: "Common Services"
3. Timeout: "abc"
4. Click "Scan"
```

**What Happens:**
```python
try:
    timeout = int(timeout_input.value.strip())  # ValueError
except ValueError:
    self.display_error("Invalid timeout value")
    return
```

**User Sees:**
```
❌ Error Message: "Invalid timeout value"
```

---

## Success Scenarios

### Example 1: Finding Open Ports

```
✓ Scan complete! Found 2 open port(s) on 192.168.1.1

Results:
Port 22  | SSH   | OPEN   | 5.2ms
Port 80  | HTTP  | OPEN   | 4.8ms
Port 443 | HTTPS | CLOSED | 3001ms

Summary: Total: 30 | Open: 2 | Closed: 27 | Filtered: 1 | Avg: 8.2ms
```

### Example 2: No Open Ports

```
✓ Scan complete on 192.168.1.100. No open ports found.

Results:
Port 22  | SSH    | CLOSED   | 3000ms
Port 80  | HTTP   | CLOSED   | 3000ms
Port 443 | HTTPS  | CLOSED   | 3000ms

Summary: Total: 30 | Open: 0 | Closed: 30 | Filtered: 0 | Avg: 3000ms
```

---

## Clear Function

### User Action:
```
Click "Clear" Button
```

### What Happens:
```python
def clear_results(self) -> None:
    host_input.value = ""                    # Clear host
    port_input.value = ""                    # Clear ports
    self.results_widget.clear_results()      # Clear table
    summary_label.update("")                 # Clear summary
    status_label.update("")                  # Clear status
    self.set_status("Ready")                 # Reset status
    self.display_success("Cleared all results")
```

### User Sees:
```
✓ Success Message: "Cleared all results"
Status Bar: "Ready"
All fields empty and ready for new scan
```

---

## Keyboard Shortcuts (Potential Future)

When integrated into main app:

```
Key     Action
────────────────────────────────
P       Open Port Scanner
S       Start Scan
C       Clear Results
T       Focus on Timeout
H       Focus on Host
M       Cycle through Modes
Escape  Close/Reset
```

---

## Performance Characteristics

### Scanning Time Estimates

**Scenario: Scan 30 common ports with 3-second timeout**

Best Case (10 open ports):
```
Time = 10 ports × 50ms avg = 500ms
Total: ~500ms
```

Worst Case (0 open ports):
```
Time = 30 ports × 3000ms (timeout) = 90 seconds
Total: ~90 seconds
Note: But concurrent workers (10) divide this
Actual: ~9 seconds (30 ÷ 10 = 3 batches × 3 seconds)
```

Typical Case (2-3 open):
```
Time: 5-15 seconds
UI remains responsive due to non-blocking async operation
```

---

## Integration with Main App

When this widget is added to the main TUI navigation:

```
Main App
├─ Dashboard
├─ DNS Resolver        (Phase 4.2)
├─ Port Scanner        (Phase 4.3) ← New!
│  └─ Full integration with app
│     • Navigation
│     • Keyboard shortcuts
│     • Status bar
│     • Error displays
│     • Success messages
├─ Latency Analyzer    (Phase 4.4)
└─ Settings
```

---

## Summary: User Experience Flow

```
1. User opens Port Scanner widget
   ↓
2. User enters target host
   ↓
3. User selects scan mode
   ↓
4. User enters ports (if applicable)
   ↓
5. User clicks "Scan"
   ↓
6. Loading indicator shows
   ↓
7. Widget scans 10 ports concurrently (non-blocking)
   ↓
8. Results displayed with color coding
   ↓
9. Summary statistics shown
   ↓
10. Success message appears
    ↓
11. User can:
    • Review results
    • Clear and scan again
    • Export results (future)
    • Compare with previous scans (future)
```

---

**This is how the Port Scanner Widget works in the real TUI application! 🚀**
