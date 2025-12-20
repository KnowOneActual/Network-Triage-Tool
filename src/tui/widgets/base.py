"""
Base Widget Classes for Phase 4 TUI Integration

This module provides the foundation for all Phase 4 widgets.
All widgets should inherit from BaseWidget to ensure consistency in:
- Error handling
- Progress tracking
- Worker management
- Result caching
- UI responsiveness
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, Optional, TypeVar
from datetime import datetime
import logging

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Label
from textual.reactive import reactive

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class OperationResult(Generic[T]):
    """Result of an async operation."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_type: Optional[type] = None
    duration_ms: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AsyncOperationMixin:
    """
    Mixin for widgets that perform async operations.
    
    Provides:
    - Safe worker execution
    - Operation cancellation
    - Error handling
    - Progress tracking
    - Result caching
    
    Usage:
        class MyWidget(BaseWidget, AsyncOperationMixin):
            async def perform_operation(self) -> OperationResult:
                try:
                    result = await self.run_in_thread(some_function)
                    return OperationResult(success=True, data=result)
                except Exception as e:
                    return self.handle_error(e)
    """
    
    def __init__(self):
        self._active_workers = {}
        self._operation_cache = {}
        self._cache_enabled = True
    
    def enable_cache(self, enabled: bool = True) -> None:
        """Enable or disable result caching."""
        self._cache_enabled = enabled
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached result if available."""
        if self._cache_enabled and key in self._operation_cache:
            return self._operation_cache[key]
        return None
    
    def cache_result(self, key: str, result: Any) -> None:
        """Cache an operation result."""
        if self._cache_enabled:
            self._operation_cache[key] = result
    
    def clear_cache(self, key: Optional[str] = None) -> None:
        """Clear cache entries."""
        if key:
            self._operation_cache.pop(key, None)
        else:
            self._operation_cache.clear()
    
    def cancel_operations(self, worker_name: Optional[str] = None) -> None:
        """Cancel active workers."""
        if worker_name and worker_name in self._active_workers:
            worker = self._active_workers[worker_name]
            if hasattr(worker, 'cancel'):
                worker.cancel()
            self._active_workers.pop(worker_name, None)
        elif not worker_name:
            for worker in self._active_workers.values():
                if hasattr(worker, 'cancel'):
                    worker.cancel()
            self._active_workers.clear()
    
    def handle_error(self, error: Exception, message: Optional[str] = None) -> OperationResult:
        """Consistent error handling."""
        error_msg = message or str(error)
        logger.error(f"Operation error: {error_msg}", exc_info=error)
        return OperationResult(
            success=False,
            error=error_msg,
            error_type=type(error)
        )


class BaseWidget(Container, AsyncOperationMixin):
    """
    Base class for all Phase 4 widgets.
    
    Provides:
    - Consistent layout and styling
    - Error handling and display
    - Progress tracking
    - Non-blocking operations via workers
    - Result caching
    - Status/health indicators
    
    All Phase 4 widgets should inherit from this class.
    
    Example:
        class DNSResolverWidget(BaseWidget):
            def compose(self) -> ComposeResult:
                yield Input(id="hostname-input")
                yield Button("Resolve", id="resolve-btn")
                yield Static(id="results")
            
            async def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "resolve-btn":
                    hostname = self.query_one("#hostname-input").value
                    self.run_worker(self._resolve(hostname))
            
            async def _resolve(self, hostname: str) -> None:
                try:
                    result = await asyncio.to_thread(resolve_hostname, hostname)
                    self.display_success(result)
                except Exception as e:
                    self.display_error(str(e))
    """
    
    # Reactive attributes for UI updates
    is_loading = reactive(False)
    current_status = reactive("Ready")
    error_message = reactive("")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        AsyncOperationMixin.__init__(self)
        self.widget_name = self.__class__.__name__
        logger.debug(f"Initializing {self.widget_name}")
    
    def compose(self) -> ComposeResult:
        """Override in subclasses to define widget layout."""
        # Default layout with error display
        yield Vertical(
            Label(f"[{self.widget_name}]", id="widget-title"),
            Static(id="error-display"),
            Static(id="content"),
            id="widget-layout"
        )
    
    def display_error(self, message: str) -> None:
        """Display error message to user."""
        self.error_message = message
        self.is_loading = False
        self.current_status = "Error"
        
        error_display = self.query_one("#error-display", expect_type=Static)
        error_display.update(f"❌ Error: {message}")
        error_display.styles.display = "block"
        
        logger.error(f"[{self.widget_name}] {message}")
    
    def display_success(self, message: str) -> None:
        """Display success message to user."""
        self.error_message = ""
        self.is_loading = False
        self.current_status = "Ready"
        
        error_display = self.query_one("#error-display", expect_type=Static)
        error_display.update("")
        error_display.styles.display = "none"
        
        logger.info(f"[{self.widget_name}] {message}")
    
    def show_loading(self, message: str = "Processing...") -> None:
        """Show loading state."""
        self.is_loading = True
        self.current_status = message
        self.error_message = ""
        logger.debug(f"[{self.widget_name}] {message}")
    
    def set_status(self, status: str) -> None:
        """Update current status."""
        self.current_status = status
        logger.debug(f"[{self.widget_name}] Status: {status}")
    
    def watch_is_loading(self, is_loading: bool) -> None:
        """React to loading state changes."""
        if is_loading:
            self.styles.opacity = 0.8
        else:
            self.styles.opacity = 1.0
    
    def watch_error_message(self, message: str) -> None:
        """React to error message changes."""
        if message:
            logger.warning(f"[{self.widget_name}] {message}")
    
    def get_result_summary(self) -> str:
        """Override in subclasses to provide result summary."""
        return f"{self.widget_name}: {self.current_status}"


class WidgetTemplate(BaseWidget):
    """
    Template for creating new Phase 4 widgets.
    
    Copy this class and customize:
    1. Update widget_name in __init__
    2. Implement compose() with your UI elements
    3. Implement event handlers (on_button_pressed, etc.)
    4. Implement async operations using AsyncOperationMixin
    
    Example:
        class MyNewWidget(WidgetTemplate):
            def __init__(self, name="MyNewWidget"):
                super().__init__(name=name)
            
            def compose(self) -> ComposeResult:
                yield Input(id="input-field")
                yield Button("Execute", id="execute-btn")
                yield DataTable(id="results-table")
    """
    
    def __init__(self, name: str = "WidgetTemplate"):
        super().__init__()
        self.widget_name = name
    
    async def async_operation(self, input_data: str) -> OperationResult[str]:
        """
        Template for async operations.
        
        Override this in subclasses with actual operation logic.
        """
        try:
            self.show_loading("Processing...")
            
            # Simulate work
            import asyncio
            await asyncio.sleep(1)
            
            result = f"Processed: {input_data}"
            return OperationResult(success=True, data=result)
        
        except Exception as e:
            return self.handle_error(e)
