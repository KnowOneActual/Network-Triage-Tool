"""Scheduler Widget for Phase 5.4."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from textual import work
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, Select, Static

from shared.latency_utils import LatencyStatus, ping_statistics

from .base import BaseWidget
from .components import ResultColumn, ResultsWidget

if TYPE_CHECKING:
    from textual.app import ComposeResult


class ScheduledTask:
    def __init__(self, id: str, target: str, task_type: str, interval: int) -> None:
        self.id = id
        self.target = target
        self.task_type = task_type
        self.interval = interval
        self.last_run: datetime.datetime | None = None
        self.last_status: str = "Pending"
        self.last_result: str = "N/A"


class SchedulerWidget(BaseWidget):
    """Widget for scheduling and monitoring regular network checks."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.widget_name = "SchedulerWidget"
        self.tasks: list[ScheduledTask] = []
        self._next_id = 1
        self._task_lock = False

    def compose(self) -> ComposeResult:
        yield Label("[bold]Scheduled Scans & Monitoring[/bold]", id="title")
        yield Static(id="error-display", classes="error-message")

        with Vertical(id="input-section"):
            yield Label("Target (IP/Hostname):")
            yield Input(id="target-input", placeholder="8.8.8.8")

            yield Label("Task Type:")
            yield Select([("Ping", "ping")], id="task-type-select", value="ping")

            yield Label("Interval (seconds):")
            yield Input(id="interval-input", placeholder="60", value="60")

            with Horizontal(id="button-section"):
                yield Button("Add Task", id="add-btn", variant="primary")
                yield Button("Clear All", id="clear-btn", variant="error")

        yield Label("[bold]Active Tasks[/bold]", id="results-title")

        columns = [
            ResultColumn("ID", "id", width=5),
            ResultColumn("Target", "target", width=20),
            ResultColumn("Type", "type", width=10),
            ResultColumn("Interval", "interval", width=10),
            ResultColumn("Last Run", "last_run", width=15),
            ResultColumn("Status", "status", width=15),
            ResultColumn("Result", "result", width=30),
        ]
        self.results_widget = ResultsWidget(columns=columns)
        yield self.results_widget

    def on_mount(self) -> None:
        self.set_interval(1.0, self.tick)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "add-btn":
                self.add_task()
            case "clear-btn":
                self.tasks.clear()
                self.update_table()

    def add_task(self) -> None:
        target = self.query_one("#target-input", Input).value.strip()
        if not target:
            self.display_error("Please enter a target")
            return

        task_type = self.query_one("#task-type-select", Select).value
        interval_str = self.query_one("#interval-input", Input).value.strip()

        try:
            interval = int(interval_str)
            if interval < 5:
                self.display_error("Interval must be at least 5 seconds")
                return
        except ValueError:
            self.display_error("Interval must be a number")
            return

        task = ScheduledTask(str(self._next_id), target, str(task_type) if task_type else "ping", interval)
        self._next_id += 1
        self.tasks.append(task)
        self.display_success(f"Added task {task.id}")
        self.update_table()

    def tick(self) -> None:
        if self._task_lock:
            return

        now = datetime.datetime.now()
        for task in self.tasks:
            if (
                task.last_run is None or (now - task.last_run).total_seconds() >= task.interval
            ) and task.last_status != "Running":
                task.last_status = "Running"
                self.update_table()
                self.run_task(task)

    @work(thread=True)
    def run_task(self, task: ScheduledTask) -> None:
        try:
            task.last_run = datetime.datetime.now()
            if task.task_type == "ping":
                stats = ping_statistics(task.target, count=4, timeout=2)
                if stats.status == LatencyStatus.SUCCESS:
                    task.last_status = "Success"
                    task.last_result = f"Avg: {stats.avg_ms:.2f}ms, Loss: {stats.packet_loss_percent:.1f}%"
                else:
                    task.last_status = "Failed"
                    task.last_result = str(stats.error_message) or "Ping failed"
            else:
                task.last_status = "Error"
                task.last_result = "Unknown task type"
        except Exception as e:
            task.last_status = "Error"
            task.last_result = str(e)

        self.app.call_from_thread(self.update_table)

    def update_table(self) -> None:
        self._task_lock = True
        self.results_widget.clear_results()
        for task in self.tasks:
            last_run_str = task.last_run.strftime("%H:%M:%S") if task.last_run else "Never"
            self.results_widget.add_result_row(
                id=task.id,
                target=task.target,
                type=task.task_type,
                interval=f"{task.interval}s",
                last_run=last_run_str,
                status=task.last_status,
                result=task.last_result,
            )
        self._task_lock = False
