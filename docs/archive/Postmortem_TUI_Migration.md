# Project Postmortem: Migrating to Textual TUI


## 1. Introduction

This document outlines the technical challenges encountered and the solutions implemented during the migration of the Network Triage Tool from a Tkinter-based GUI to a Textual-based Terminal User Interface (TUI). The primary motivation was to resolve persistent cross-platform stability issues, particularly on macOS, and to create a more robust, developer-friendly tool that could operate over SSH.


## 2. Key Challenges & Solutions


### Challenge 1: Cross-Platform Stability & Distribution

The Problem: The original Tkinter application suffered from stability issues on macOS and Windows. Packaging it with PyInstaller was complex and prone to "silent crashes" due to permission handling and hidden dependencies.

The Solution: We pivoted to a TUI using the Textual framework.



* **Why:** TUIs run natively in the terminal, bypassing the complexities of windowing systems (Quartz/X11/Win32).
* **Benefit:** This allows for easy distribution via pip and enables the tool to be used in headless environments (SSH).


### Challenge 2: UI Freezing During Long-Running Tasks

The Problem: Network operations like continuous_ping and speedtest-cli are blocking operations. In the Tkinter version, complex threading logic was required to prevent the UI from freezing ("Not Responding") while these tests ran.

The Solution: Implemented Textual Workers using the @work decorator.



* **Why:** Textual's worker API abstracts away thread management. By simply decorating a method with @work(thread=True), the framework automatically runs it in a background thread.
* **Benefit:** The UI remains fully responsive. Users can switch tabs and view the dashboard while a ping or speed test continues to run in the background.


### Challenge 3: Speedtest API Blocking (403 Forbidden)

The Problem: The speedtest-cli library began failing with HTTP Error 403: Forbidden. This was due to speedtest.net servers blocking the default (non-secure) connection method used by the library.

The Solution: Enforced HTTPS in the backend logic.



* **Fix:** Updated src/shared/shared_toolkit.py to initialize the speedtest object with secure=True. \
st = speedtest.Speedtest(secure=True) \



### Challenge 4: CSS Layout & Visibility Issues

**The Problem:** We faced significant difficulty getting the navigation tabs to render correctly.



1. **Invisible Text:** Default styling caused white-on-white or black-on-black text, making tabs invisible.
2. **Layout Collisions:** The Header (docked to top) and Tabs (also docked to top) fought for the same screen space, causing the tabs to be hidden behind the header or pushed off-screen.
3. **Terminal Compatibility:** Font sizing and layout assumptions from web development (like border-radius or font-size) caused crashes in the terminal environment.

**The Solution:** A simplified, "Manual Navigation" approach with a High-Contrast Theme.



* **Manual Nav:** We abandoned the complex TabbedContent widget in favor of a simple row of Button widgets. This removed the "magic" layout logic that was failing.
* **Explicit Styling:** We created a src/triage.tcss theme that enforces high-contrast colors (Safety Palette) and explicit spacing (padding/margins) to guarantee visibility.
* **Flow Layout:** We stopped over-using dock: top and instead let elements flow naturally (Header -> Nav Bar -> Content), using margins to prevent overlap.


## 3. Architectural Changes


<table>
  <tr>
   <td><strong>Feature</strong>
   </td>
   <td><strong>Old Architecture (Tkinter)</strong>
   </td>
   <td><strong>New Architecture (Textual)</strong>
   </td>
  </tr>
  <tr>
   <td><strong>UI Engine</strong>
   </td>
   <td>tkinter / ttkbootstrap
   </td>
   <td>textual
   </td>
  </tr>
  <tr>
   <td><strong>Concurrency</strong>
   </td>
   <td>Manual threading.Thread
   </td>
   <td>Textual @work Decorator
   </td>
  </tr>
  <tr>
   <td><strong>Navigation</strong>
   </td>
   <td>ttk.Notebook
   </td>
   <td>Manual Button Bar + ContentSwitcher
   </td>
  </tr>
  <tr>
   <td><strong>Styling</strong>
   </td>
   <td>Python-based configuration
   </td>
   <td>CSS (.tcss)
   </td>
  </tr>
  <tr>
   <td><strong>Entry Point</strong>
   </td>
   <td>src.macos.main_app
   </td>
   <td>src.tui_app
   </td>
  </tr>
</table>



## 4. Conclusion

The migration to Textual has successfully resolved the stability and distribution blockers. While the learning curve for TUI layouts (specifically CSS in a terminal context) presented challenges, the resulting application is significantly more robust. It now adheres to the "Unix Philosophy" of being a lightweight, composable tool that does one thing well, regardless of the operating system.
