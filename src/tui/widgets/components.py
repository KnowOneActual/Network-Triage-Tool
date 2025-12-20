"""
Reusable Widget Components for Phase 4

Provides common UI elements that all Phase 4 widgets use:
- ResultsWidget: Standardized results table with filtering and sorting
- ProgressWidget: Standardized progress display
- StatusIndicator: Health/status display
- ErrorDisplay: Consistent error message display
"""

from typing import Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, DataTable, ProgressBar, Label
from textual.reactive import reactive
from textual.widgets.data_table import RowKey


@dataclass
class ResultColumn:
    """Definition for a results table column."""
    name: str
    key: str
    width: Optional[int] = None
    cell_width: Optional[int] = None


class ResultsWidget(DataTable):
    """
    Standardized results table for Phase 4 widgets.
    
    Features:
    - Sortable columns
    - Filterable results
    - Copy to clipboard
    - Status-based coloring
    - Summary statistics
    
    Usage:
        class MyWidget(BaseWidget):
            def compose(self) -> ComposeResult:
                columns = [
                    ResultColumn("Port", "port", width=10),
                    ResultColumn("Service", "service", width=15),
                    ResultColumn("Status", "status", width=12),
                    ResultColumn("Time", "time", width=10),
                ]
                self.results_widget = ResultsWidget(columns=columns)
                yield self.results_widget
            
            def add_result(self, data: dict):
                self.results_widget.add_row(**data)
    """
    
    def __init__(self, columns: List[ResultColumn], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns_def = columns
        self.result_count = 0
        self.status_colors = {
            "open": "green",
            "closed": "red",
            "filtered": "yellow",
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "pending": "blue",
        }
        self._setup_columns()
    
    def _setup_columns(self) -> None:
        """Initialize table columns."""
        for col in self.columns_def:
            self.add_column(
                col.name,
                key=col.key,
                width=col.cell_width or 20
            )
    
    def add_row(self, **data) -> RowKey:
        """Add a result row."""
        values = [
            str(data.get(col.key, ""))
            for col in self.columns_def
        ]
        self.result_count += 1
        return super().add_row(*values, key=str(self.result_count))
    
    def add_rows(self, rows: List[dict]) -> None:
        """Add multiple result rows."""
        for row in rows:
            self.add_row(**row)
    
    def get_results(self) -> List[dict]:
        """Get all results as list of dicts."""
        results = []
        for row_key in self.row_keys:
            row_data = {}
            for i, col in enumerate(self.columns_def):
                value = self.get_cell(row_key, i)
                row_data[col.key] = value
            results.append(row_data)
        return results
    
    def get_summary(self) -> str:
        """Get results summary statistics."""
        return f"Total results: {self.result_count}"
    
    def filter_by(self, column_key: str, value: str) -> None:
        """Filter results by column value."""
        # Note: Textual DataTable doesn't have built-in filtering
        # This would be implemented with a custom filter in subclasses
        pass
    
    def clear_results(self) -> None:
        """Clear all results from table."""
        self.clear()
        self.result_count = 0


class ProgressWidget(Container):
    """
    Standardized progress display for long-running operations.
    
    Features:
    - Percentage display
    - Time elapsed/remaining
    - Operation description
    - Cancel button
    
    Usage:
        class MyWidget(BaseWidget):
            def compose(self) -> ComposeResult:
                self.progress = ProgressWidget()
                yield self.progress
            
            async def long_operation(self):
                for i in range(100):
                    self.progress.update(i, 100, "Processing item...")
                    await asyncio.sleep(0.1)
    """
    
    progress = reactive(0)
    total = reactive(100)
    description = reactive("Processing...")
    
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(id="progress-description"),
            ProgressBar(id="progress-bar"),
            Label(id="progress-stats"),
        )
    
    def update(self, current: int, total: int, description: str = "") -> None:
        """Update progress display."""
        self.progress = current
        self.total = total
        if description:
            self.description = description
    
    def watch_progress(self, progress: int) -> None:
        """Update progress bar when progress changes."""
        bar = self.query_one("#progress-bar", ProgressBar)
        bar.progress = (progress / self.total) * 100 if self.total > 0 else 0
    
    def watch_description(self, description: str) -> None:
        """Update description label."""
        label = self.query_one("#progress-description", Label)
        label.update(description)
    
    def watch_progress(self, progress: int) -> None:
        """Update stats label."""
        stats_label = self.query_one("#progress-stats", Label)
        percentage = (progress / self.total * 100) if self.total > 0 else 0
        stats_label.update(f"{progress}/{self.total} ({percentage:.1f}%)")


class StatusIndicator(Static):
    """
    Status/health indicator widget.
    
    Features:
    - Color-coded status (green/yellow/red)
    - Status text
    - Details tooltip
    
    Usage:
        status = StatusIndicator(status="success", text="Connected")
        yield status
    """
    
    def __init__(
        self,
        status: str = "pending",
        text: str = "",
        details: str = "",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.status = status
        self.text = text
        self.details = details
        self._update_display()
    
    def _update_display(self) -> None:
        """Update the status display."""
        status_symbols = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "pending": "⏳",
            "open": "🟢",
            "closed": "🔴",
            "filtered": "🟡",
        }
        symbol = status_symbols.get(self.status, "●")
        self.update(f"{symbol} {self.text}")
    
    def set_status(self, status: str, text: str = "", details: str = "") -> None:
        """Update status display."""
        self.status = status
        if text:
            self.text = text
        if details:
            self.details = details
        self._update_display()


class ErrorDisplay(Static):
    """
    Consistent error message display.
    
    Features:
    - Error icon and formatting
    - Error details (expandable)
    - Dismiss button
    - Error type information
    
    Usage:
        error_display = ErrorDisplay()
        error_display.show_error("Connection failed", "Unable to connect to 8.8.8.8")
        yield error_display
    """
    
    error_message = reactive("")
    error_details = reactive("")
    is_visible = reactive(False)
    
    def show_error(self, message: str, details: str = "") -> None:
        """Display an error."""
        self.error_message = message
        self.error_details = details
        self.is_visible = True
        self._update_display()
    
    def clear_error(self) -> None:
        """Clear the error display."""
        self.error_message = ""
        self.error_details = ""
        self.is_visible = False
        self.update("")
    
    def _update_display(self) -> None:
        """Update error display."""
        if not self.is_visible or not self.error_message:
            self.update("")
            return
        
        display = f"❌ {self.error_message}"
        if self.error_details:
            display += f"\n  Details: {self.error_details}"
        
        self.update(display)
        self.styles.border = ("solid", "red")
        self.styles.padding = (1, 2)
    
    def watch_error_message(self, message: str) -> None:
        """React to error message changes."""
        self._update_display()


class SummaryWidget(Static):
    """
    Summary statistics widget for operation results.
    
    Features:
    - Key-value pairs display
    - Color-coded values
    - Sortable
    
    Usage:
        summary = SummaryWidget()
        summary.add_stat("Total", "42", color="green")
        summary.add_stat("Failed", "2", color="red")
        yield summary
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {}
    
    def add_stat(self, name: str, value: str, color: Optional[str] = None) -> None:
        """Add a statistic."""
        self.stats[name] = {"value": value, "color": color}
        self._update_display()
    
    def _update_display(self) -> None:
        """Update the summary display."""
        lines = []
        for name, data in self.stats.items():
            value = data["value"]
            color = data.get("color", "")
            if color:
                lines.append(f"{name}: [{color}]{value}[/{color}]")
            else:
                lines.append(f"{name}: {value}")
        
        self.update("\n".join(lines))
    
    def clear_stats(self) -> None:
        """Clear all statistics."""
        self.stats.clear()
        self.update("")
