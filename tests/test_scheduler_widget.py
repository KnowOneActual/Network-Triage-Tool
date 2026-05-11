from unittest.mock import MagicMock, patch

import pytest
from textual.app import App, ComposeResult

from tui.widgets.scheduler_widget import ScheduledTask, SchedulerWidget


class SchedulerApp(App):
    def compose(self) -> ComposeResult:
        yield SchedulerWidget()


@pytest.mark.asyncio
async def test_scheduler_widget_mount():
    app = SchedulerApp()
    async with app.run_test() as pilot:
        widget = app.query_one(SchedulerWidget)
        assert widget is not None
        assert widget.tasks == []


@pytest.mark.asyncio
async def test_scheduler_widget_add_task():
    app = SchedulerApp()
    async with app.run_test() as pilot:
        widget = app.query_one(SchedulerWidget)

        # Valid input
        target_input = widget.query_one("#target-input")
        target_input.value = "8.8.8.8"

        interval_input = widget.query_one("#interval-input")
        interval_input.value = "10"

        await pilot.click("#add-btn")
        assert len(widget.tasks) == 1
        assert widget.tasks[0].target == "8.8.8.8"
        assert widget.tasks[0].interval == 10


@pytest.mark.asyncio
async def test_scheduler_widget_add_invalid_task():
    app = SchedulerApp()
    async with app.run_test() as pilot:
        widget = app.query_one(SchedulerWidget)

        # Empty target
        await pilot.click("#add-btn")
        assert len(widget.tasks) == 0

        # valid target, invalid interval (letters)
        await pilot.click("#target-input")
        await pilot.press("8", ".", "8", ".", "8", ".", "8")

        await pilot.click("#interval-input")
        for _ in range(5):
            await pilot.press("backspace")
        await pilot.press("a", "b", "c")

        await pilot.click("#add-btn")
        assert len(widget.tasks) == 0

        # Valid target, invalid interval (< 5)
        await pilot.click("#interval-input")
        for _ in range(5):
            await pilot.press("backspace")
        await pilot.press("2")

        await pilot.click("#add-btn")
        assert len(widget.tasks) == 0


@pytest.mark.asyncio
async def test_scheduler_widget_clear():
    app = SchedulerApp()
    async with app.run_test() as pilot:
        widget = app.query_one(SchedulerWidget)

        widget.tasks.append(ScheduledTask("1", "8.8.8.8", "ping", 60))
        await pilot.click("#clear-btn")
        assert len(widget.tasks) == 0


@pytest.mark.asyncio
async def test_scheduler_widget_tick_and_run(monkeypatch):
    import datetime

    from shared.latency_utils import LatencyStatus

    mock_stats = MagicMock()
    mock_stats.status = LatencyStatus.SUCCESS
    mock_stats.avg_ms = 10.0
    mock_stats.packet_loss_percent = 0.0

    app = SchedulerApp()
    async with app.run_test() as pilot:
        widget = app.query_one(SchedulerWidget)
        task = ScheduledTask("1", "8.8.8.8", "ping", 60)
        # Force the task to run now
        task.last_run = datetime.datetime.now() - datetime.timedelta(seconds=100)
        widget.tasks.append(task)

        with patch("tui.widgets.scheduler_widget.ping_statistics", return_value=mock_stats):
            widget.tick()
            await pilot.pause(0.1)  # allow worker to run

        assert task.last_status == "Success"
        assert task.last_result == "Avg: 10.00ms, Loss: 0.0%"


@pytest.mark.asyncio
async def test_scheduler_widget_tick_and_run_failure(monkeypatch):
    import datetime

    from shared.latency_utils import LatencyStatus

    mock_stats = MagicMock()
    mock_stats.status = LatencyStatus.ERROR
    mock_stats.error_message = "Mocked failure"

    app = SchedulerApp()
    async with app.run_test() as pilot:
        widget = app.query_one(SchedulerWidget)
        task = ScheduledTask("1", "8.8.8.8", "ping", 60)
        # Force the task to run now
        task.last_run = datetime.datetime.now() - datetime.timedelta(seconds=100)
        widget.tasks.append(task)

        with patch("tui.widgets.scheduler_widget.ping_statistics", return_value=mock_stats):
            widget.tick()
            await pilot.pause(0.1)

        assert task.last_status == "Failed"
        assert task.last_result == "Mocked failure"


@pytest.mark.asyncio
async def test_scheduler_widget_tick_unknown_type():
    import datetime

    app = SchedulerApp()
    async with app.run_test() as pilot:
        widget = app.query_one(SchedulerWidget)
        task = ScheduledTask("1", "8.8.8.8", "unknown", 60)
        task.last_run = datetime.datetime.now() - datetime.timedelta(seconds=100)
        widget.tasks.append(task)

        widget.tick()
        await pilot.pause(0.1)

        assert task.last_status == "Error"
        assert task.last_result == "Unknown task type"
