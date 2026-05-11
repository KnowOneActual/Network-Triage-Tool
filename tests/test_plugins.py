from unittest.mock import MagicMock, patch

from textual.containers import Container

from network_triage.plugins import load_plugins


class DummyPlugin:
    @property
    def id(self) -> str:
        return "dummy"

    @property
    def name(self) -> str:
        return "Dummy"

    @property
    def icon(self) -> str:
        return "🔨"

    def get_widget(self) -> Container:
        return Container()

    def get_report_data(self) -> str | None:
        return "Dummy report data"


class BadPlugin:
    pass


def test_load_plugins_success():
    mock_ep = MagicMock()
    mock_ep.name = "dummy"
    mock_ep.load.return_value = DummyPlugin

    with patch("importlib.metadata.entry_points") as mock_entry_points:
        mock_entry_points.return_value = [mock_ep]
        plugins = load_plugins()
        assert len(plugins) == 1
        assert plugins[0].id == "dummy"
        assert plugins[0].get_report_data() == "Dummy report data"


def test_load_plugins_bad_plugin():
    mock_ep = MagicMock()
    mock_ep.name = "bad"
    mock_ep.load.return_value = BadPlugin

    with patch("importlib.metadata.entry_points") as mock_entry_points:
        mock_entry_points.return_value = [mock_ep]
        plugins = load_plugins()
        assert len(plugins) == 0


def test_load_plugins_load_exception():
    mock_ep = MagicMock()
    mock_ep.name = "error"
    mock_ep.load.side_effect = Exception("Load failed")

    with patch("importlib.metadata.entry_points") as mock_entry_points:
        mock_entry_points.return_value = [mock_ep]
        plugins = load_plugins()
        assert len(plugins) == 0
