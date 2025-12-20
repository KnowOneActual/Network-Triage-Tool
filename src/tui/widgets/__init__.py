"""
TUI Widgets Package

This package contains all Textual widgets for the Network Triage Tool.
Phase 4 integrates Phase 3 diagnostics utilities into interactive widgets.

Widget Architecture:
- BaseWidget: Foundation class for all Phase 4 widgets
- AsyncOperationMixin: Patterns for non-blocking operations
- Reusable components: ResultsWidget, ProgressWidget, StatusIndicator

All widgets follow these patterns:
1. Non-blocking operations via Textual workers
2. Consistent error handling
3. Progress tracking and cancellation support
4. Result caching for performance
"""

from .base import BaseWidget, AsyncOperationMixin
from .components import ResultsWidget, ProgressWidget, StatusIndicator

__all__ = [
    "BaseWidget",
    "AsyncOperationMixin",
    "ResultsWidget",
    "ProgressWidget",
    "StatusIndicator",
]
