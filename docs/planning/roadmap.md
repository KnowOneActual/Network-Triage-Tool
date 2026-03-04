# Project Roadmap

## Vision

Build a comprehensive, professional-grade Network Triage Tool with:
1. Solid diagnostic foundation (Phase 3: Complete)
2. Intuitive TUI widget integration (Phase 4: In Progress)
3. Advanced analysis and visualization (Phase 5+: Future)

---

## Phase 1: macOS Stabilization ✅ COMPLETE
**Status:** COMPLETE - Ready for production use

---

## Phase 2: TUI Framework ✅ COMPLETE
**Status:** COMPLETE - Shipped in v0.2.0+

---

## Phase 3: Advanced Diagnostics ✅ COMPLETE (v0.3.0)
**Status:** COMPLETE - Shipped in v0.3.0

---

## Phase 4: TUI Widget Integration 🚀 IN PROGRESS (v0.4.0)

**Goal:** Integrate Phase 3 diagnostics and new professional triage tools into reusable TUI widgets.

### Phase 4.1: Widget Foundation ✅ COMPLETE
### Phase 4.2: DNS Resolver Widget ✅ COMPLETE
### Phase 4.3: Port Scanner Widget ✅ COMPLETE

### Phase 4.4: Live Path Analyzer (MTR-style) 🔜 NEXT
**Professional Path Diagnostics:**
- [ ] Live-updating hop table (replaces static Traceroute)
- [ ] Real-time Latency (Min/Max/Avg) per hop
- [ ] Packet Loss percentage tracking per hop
- [ ] Jitter analysis for every point in the path
- [ ] Visual indicators for where bottlenecks begin

### Phase 4.5: Connection Monitor (Active Sockets) 🔜 PLANNED
**Resource Triage:**
- [ ] Live list of active TCP/UDP connections (SS/Netstat style)
- [ ] Remote IP/Port and local process identification
- [ ] Connection state tracking (ESTABLISHED, TIME_WAIT, etc.)
- [ ] Quick-filter for high-bandwidth connections

### Phase 4.6: LAN Bandwidth Tester (Internal Performance) 🔜 PLANNED
**Local Network Diagnostics:**
- [ ] Iperf3-lite client integration
- [ ] Peer-to-peer LAN speed testing (Internal vs. Internet delta)
- [ ] Bandwidth saturation benchmarking

---

## Phase 5: Advanced Features 🎯 FUTURE

**Goal:** Add high-level visualization and broadcast monitoring.

### Live Protocol Summary (Traffic "Health")
- [ ] Passive broadcast counter (DHCP, ARP, STP, LLDP)
- [ ] Real-time traffic type distribution (broadcast vs. unicast)
- [ ] *Note: Focused on summary stats, not full packet capture.*

### Results History & Export
- [ ] CSV/JSON/PDF reporting
- [ ] Historical comparison (Yesterday vs. Today)

---

## 🚫 Features to Drop / Exclude (The "Triage" Principle)

To maintain focus and high performance, the following features are **explicitly excluded**:

1.  **Full Packet Inspection (Deep DPI):** We will NOT implement a Wireshark-style full packet viewer. It causes "information overload" and is too heavy for a quick triage tool. We focus on counters and summaries only.
2.  **Heavy Nmap Flags:** We will NOT support Nmap scripting engines (NSE) or aggressive OS fingerprinting by default. These are too slow and can trigger security alerts. We stay focused on "Is it open or closed?"
3.  **Complex Configuration:** No heavy configuration files or database setups. The tool must be "Zero Config" and ready to run immediately.

---

## Current Status Summary

| Phase | Status | Feature | Notes |
|-------|--------|---------|-------|
| 4.1 | ✅ | Foundation | Solid BaseWidget pattern |
| 4.2 | ✅ | DNS Resolver | Multi-provider support |
| 4.3 | ✅ | Port Scanner | Concurrent scanning |
| 4.4 | 🔜 | Path Analyzer | **High Priority: MTR-style** |
| 4.5 | 🔜 | Conn Monitor | Identifying local hogs |
| 4.6 | 🔜 | LAN Tester | Internal vs External delta |
| 5.0 | 🎯 | Traffic Health | Broadcast summaries |

**Total Tests:** 184 items passing 🎉
