"""Tests for NetworkTriageApp using Textual's testing framework.

Verifies the main UI components and tab switching functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import network_triage.app

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

# Create a robust mock toolkit
mock_toolkit = MagicMock()
mock_toolkit.get_system_info.return_value = {"OS": "Test OS", "Hostname": "Test-Host"}
mock_toolkit.get_ip_info.return_value = {
    "Internal IP": "127.0.0.1",
    "Gateway": "127.0.0.1",
    "Public IP": "1.1.1.1",
}
mock_toolkit.get_connection_details.return_value = {"Interface": "lo0", "Status": "Up"}
mock_toolkit.health_check.return_value = {"status": "healthy", "components": {"ping": True}}

# Apply the mock to the module-level variable
network_triage.app.net_tool = mock_toolkit

from network_triage.app import NetworkTriageApp


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_app_startup() -> None:
    """Test that the app starts up and displays core components."""
    from textual.widgets import ContentSwitcher, Footer, Header

    app = NetworkTriageApp()
    async with app.run_test() as pilot:
        # Give background tasks time to complete
        await pilot.pause(0.5)

        # Check for main components
        assert app.query_one(Header)
        assert app.query_one(Footer)
        assert app.query_one("#content_box", ContentSwitcher)

        # Verify mocked data is displayed
        hostname_box: Any = app.query_one("#info_hostname")
        assert hostname_box.value_text == "Test-Host"


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_tab_switching() -> None:
    """Test switching between different diagnostic tabs."""
    from textual.widgets import ContentSwitcher

    app = NetworkTriageApp()
    async with app.run_test() as pilot:
        # Wait for app to be ready
        await pilot.pause(0.2)
        switcher = app.query_one("#content_box", ContentSwitcher)

        # Switch to Connection Info
        await pilot.press("c")
        await pilot.pause(0.1)
        assert switcher.current == "connection"

        # Switch to Ping
        await pilot.press("p")
        await pilot.pause(0.1)
        assert switcher.current == "ping"

        # Switch to Utilities (u key)
        await pilot.press("u")
        await pilot.pause(0.1)
        assert switcher.current == "utils"


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_info_box_click_clipboard(mocker: MockerFixture) -> None:
    """Test that clicking an InfoBox copies to clipboard."""
    app = NetworkTriageApp()
    # Mock notify and copy_to_clipboard
    mock_notify = mocker.patch.object(app, "notify")
    mock_copy = mocker.patch.object(app, "copy_to_clipboard")

    async with app.run_test() as pilot:
        from network_triage.app import InfoBox

        box = app.query_one("#info_internal_ip", InfoBox)
        box.value_text = "192.168.1.1"

        await pilot.click("#info_internal_ip")

        mock_copy.assert_called_with("192.168.1.1")
        mock_notify.assert_called()
