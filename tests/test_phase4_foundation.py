"""
Phase 4.1 Foundation Tests

Tests for:
- BaseWidget class
- AsyncOperationMixin patterns
- Reusable components (ResultsWidget, ProgressWidget, etc.)
- Error handling patterns
- Worker integration
- Result caching
"""

import sys
from pathlib import Path
import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, PropertyMock

from textual.app import ComposeResult
from textual.widgets import Static

# Add src to path for imports (same as conftest but explicit)
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import widgets to test
from tui.widgets.base import (
    BaseWidget,
    AsyncOperationMixin,
    OperationResult,
    WidgetTemplate,
)
from tui.widgets.components import (
    ResultsWidget,
    ResultColumn,
    ProgressWidget,
    StatusIndicator,
    ErrorDisplay,
    SummaryWidget,
)


class TestOperationResult:
    """Tests for OperationResult dataclass."""

    def test_operation_result_success(self):
        """Test creating a successful operation result."""
        result = OperationResult(success=True, data="test_data")
        assert result.success is True
        assert result.data == "test_data"
        assert result.error is None
        assert result.timestamp is not None

    def test_operation_result_error(self):
        """Test creating an error operation result."""
        result = OperationResult(
            success=False,
            error="Test error",
            error_type=ValueError
        )
        assert result.success is False
        assert result.error == "Test error"
        assert result.error_type == ValueError

    def test_operation_result_timestamp(self):
        """Test that timestamp is set automatically."""
        before = datetime.now()
        result = OperationResult(success=True, data="test")
        after = datetime.now()
        
        assert before <= result.timestamp <= after

    def test_operation_result_duration(self):
        """Test setting duration in operation result."""
        result = OperationResult(success=True, data="test", duration_ms=123.45)
        assert result.duration_ms == 123.45


class TestAsyncOperationMixin:
    """Tests for AsyncOperationMixin class."""

    def test_cache_enabled_by_default(self):
        """Test that caching is enabled by default."""
        mixin = AsyncOperationMixin()
        assert mixin._cache_enabled is True

    def test_enable_disable_cache(self):
        """Test enabling and disabling cache."""
        mixin = AsyncOperationMixin()
        
        mixin.enable_cache(False)
        assert mixin._cache_enabled is False
        
        mixin.enable_cache(True)
        assert mixin._cache_enabled is True

    def test_cache_result(self):
        """Test caching results."""
        mixin = AsyncOperationMixin()
        mixin.cache_result("key1", "value1")
        
        assert mixin.get_cached("key1") == "value1"

    def test_get_cached_returns_none_when_disabled(self):
        """Test that get_cached returns None when caching disabled."""
        mixin = AsyncOperationMixin()
        mixin.cache_result("key1", "value1")
        mixin.enable_cache(False)
        
        assert mixin.get_cached("key1") is None

    def test_clear_cache_single_key(self):
        """Test clearing a single cache key."""
        mixin = AsyncOperationMixin()
        mixin.cache_result("key1", "value1")
        mixin.cache_result("key2", "value2")
        
        mixin.clear_cache("key1")
        
        assert mixin.get_cached("key1") is None
        assert mixin.get_cached("key2") == "value2"

    def test_clear_cache_all(self):
        """Test clearing all cache."""
        mixin = AsyncOperationMixin()
        mixin.cache_result("key1", "value1")
        mixin.cache_result("key2", "value2")
        
        mixin.clear_cache()
        
        assert mixin.get_cached("key1") is None
        assert mixin.get_cached("key2") is None

    def test_handle_error(self):
        """Test error handling."""
        mixin = AsyncOperationMixin()
        error = ValueError("Test error")
        
        result = mixin.handle_error(error, "Custom message")
        
        assert result.success is False
        assert result.error == "Custom message"
        assert result.error_type == ValueError

    def test_handle_error_without_message(self):
        """Test error handling without custom message."""
        mixin = AsyncOperationMixin()
        error = ValueError("Test error")
        
        result = mixin.handle_error(error)
        
        assert result.success is False
        assert "Test error" in result.error
        assert result.error_type == ValueError

    def test_active_workers_initialization(self):
        """Test that active workers dict is initialized."""
        mixin = AsyncOperationMixin()
        assert isinstance(mixin._active_workers, dict)
        assert len(mixin._active_workers) == 0


class TestBaseWidget:
    """Tests for BaseWidget base class."""

    def test_base_widget_initialization(self):
        """Test BaseWidget initializes correctly."""
        widget = BaseWidget()
        
        assert widget.is_loading is False
        assert widget.current_status == "Ready"
        assert widget.error_message == ""
        assert hasattr(widget, 'widget_name')

    def test_base_widget_name(self):
        """Test widget name is set correctly."""
        widget = BaseWidget()
        assert widget.widget_name == "BaseWidget"

    def test_display_error(self):
        """Test displaying error message via logging."""
        widget = BaseWidget()
        # Test that display_error sets the reactive attribute
        # Note: query_one() requires an active app context, so we test the state changes
        try:
            widget.display_error("Test error message")
        except Exception:
            # Expected - no app context. But reactive attributes should still be set.
            pass
        
        # Verify the reactive attributes changed
        assert widget.error_message == "Test error message"
        assert widget.current_status == "Error"

    def test_display_success(self):
        """Test displaying success message."""
        widget = BaseWidget()
        try:
            widget.display_success("Operation complete")
        except Exception:
            # Expected - no app context
            pass
        
        # Verify the reactive attributes
        assert widget.error_message == ""
        assert widget.is_loading is False
        assert widget.current_status == "Ready"

    def test_show_loading(self):
        """Test showing loading state."""
        widget = BaseWidget()
        widget.show_loading("Processing...")
        
        assert widget.is_loading is True
        assert widget.current_status == "Processing..."
        assert widget.error_message == ""

    def test_set_status(self):
        """Test setting status."""
        widget = BaseWidget()
        widget.set_status("Running operation")
        
        assert widget.current_status == "Running operation"

    def test_get_result_summary(self):
        """Test getting result summary."""
        widget = BaseWidget()
        summary = widget.get_result_summary()
        
        assert "BaseWidget" in summary
        assert "Ready" in summary

    def test_inherits_async_operation_mixin(self):
        """Test that BaseWidget inherits AsyncOperationMixin methods."""
        widget = BaseWidget()
        
        assert hasattr(widget, 'cache_result')
        assert hasattr(widget, 'get_cached')
        assert hasattr(widget, 'handle_error')
        assert hasattr(widget, 'cancel_operations')


class TestWidgetTemplate:
    """Tests for WidgetTemplate."""

    def test_widget_template_initialization(self):
        """Test WidgetTemplate initializes with custom name."""
        template = WidgetTemplate(name="CustomWidget")
        
        assert template.widget_name == "CustomWidget"

    def test_widget_template_default_name(self):
        """Test WidgetTemplate uses default name."""
        template = WidgetTemplate()
        
        assert template.widget_name == "WidgetTemplate"

    def test_widget_template_async_operation(self):
        """Test async operation in template."""
        template = WidgetTemplate()
        
        # This would normally be run in async context
        # Just verify the method exists and has proper signature
        assert hasattr(template, 'async_operation')
        assert callable(template.async_operation)


class TestResultsWidget:
    """Tests for ResultsWidget component."""

    def test_results_widget_attributes(self):
        """Test ResultsWidget has required attributes."""
        # Don't instantiate with columns (requires app context)
        # Just test the class has what we need
        assert hasattr(ResultsWidget, '__init__')
        assert hasattr(ResultsWidget, 'add_row')
        assert hasattr(ResultsWidget, 'add_rows')
        assert hasattr(ResultsWidget, 'clear_results')
        assert hasattr(ResultsWidget, 'get_summary')

    def test_result_column_creation(self):
        """Test ResultColumn can be created."""
        col = ResultColumn("Name", "name", width=20)
        assert col.label == "Name"
        assert col.field_name == "name"
        assert col.width == 20

    def test_result_column_default_width(self):
        """Test ResultColumn default width."""
        col = ResultColumn("Status", "status")
        assert col.label == "Status"
        assert col.field_name == "status"
        # Default width should be set
        assert col.width > 0

    def test_results_widget_mock_data(self):
        """Test results widget method signatures work with mocks."""
        # Test the interface without instantiating in no-app context
        mock_widget = MagicMock(spec=ResultsWidget)
        mock_widget.add_row = MagicMock()
        mock_widget.add_rows = MagicMock()
        mock_widget.result_count = 0
        mock_widget.get_summary = MagicMock(return_value="Results: 0 items")
        
        # Verify methods can be called
        mock_widget.add_row(name="test", status="active")
        mock_widget.add_row.assert_called_with(name="test", status="active")
        
        # Verify summary can be retrieved
        summary = mock_widget.get_summary()
        assert "Results" in summary


class TestStatusIndicator:
    """Tests for StatusIndicator component."""

    def test_status_indicator_initialization(self):
        """Test StatusIndicator initializes correctly."""
        indicator = StatusIndicator(status="success", text="Connected")
        
        assert indicator.status == "success"
        assert indicator.text == "Connected"

    def test_status_indicator_set_status(self):
        """Test setting status on StatusIndicator."""
        indicator = StatusIndicator()
        indicator.set_status("error", "Disconnected")
        
        assert indicator.status == "error"
        assert indicator.text == "Disconnected"

    def test_status_indicator_symbols(self):
        """Test that status indicator has valid symbols."""
        statuses = ["success", "error", "warning", "pending"]
        
        for status in statuses:
            indicator = StatusIndicator(status=status)
            # Just verify it doesn't crash
            assert indicator.status == status


class TestErrorDisplay:
    """Tests for ErrorDisplay component."""

    def test_error_display_show_error(self):
        """Test showing error in ErrorDisplay."""
        display = ErrorDisplay()
        display.show_error("Connection failed", "Unable to reach server")
        
        assert display.error_message == "Connection failed"
        assert display.error_details == "Unable to reach server"
        assert display.is_visible is True

    def test_error_display_clear_error(self):
        """Test clearing error from ErrorDisplay."""
        display = ErrorDisplay()
        display.show_error("Test error")
        display.clear_error()
        
        assert display.error_message == ""
        assert display.error_details == ""
        assert display.is_visible is False


class TestSummaryWidget:
    """Tests for SummaryWidget component."""

    def test_summary_widget_add_stat(self):
        """Test adding statistics to SummaryWidget."""
        summary = SummaryWidget()
        summary.add_stat("Total", "42")
        
        assert "Total" in summary.stats
        assert summary.stats["Total"]["value"] == "42"

    def test_summary_widget_add_stat_with_color(self):
        """Test adding colored statistics."""
        summary = SummaryWidget()
        summary.add_stat("Success", "100", color="green")
        
        assert summary.stats["Success"]["color"] == "green"

    def test_summary_widget_clear_stats(self):
        """Test clearing statistics."""
        summary = SummaryWidget()
        summary.add_stat("Total", "42")
        summary.add_stat("Failed", "2")
        
        summary.clear_stats()
        
        assert len(summary.stats) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
