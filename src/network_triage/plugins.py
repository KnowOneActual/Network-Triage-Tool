import importlib.metadata
import logging
from typing import Protocol, runtime_checkable

from textual.containers import Container

logger = logging.getLogger(__name__)


@runtime_checkable
class TUIPlugin(Protocol):
    """Protocol for Network Triage Tool plugins."""

    @property
    def id(self) -> str:
        """Unique identifier for the plugin (e.g., 'my_plugin')."""
        ...

    @property
    def name(self) -> str:
        """Display name for the plugin (e.g., 'My Plugin')."""
        ...

    @property
    def icon(self) -> str:
        """Emoji or short string for the navigation bar."""
        ...

    def get_widget(self) -> Container:
        """Return the Textual Container widget for this plugin."""
        ...

    def get_report_data(self) -> str | None:
        """Return optional report data to include in the triage report."""
        return None


def load_plugins() -> list[TUIPlugin]:
    """Discover and load plugins registered via entry points."""
    plugins = []

    eps = importlib.metadata.entry_points(group="network_triage.widgets")

    for ep in eps:
        try:
            plugin_class = ep.load()
            plugin_instance = plugin_class()

            if not isinstance(plugin_instance, TUIPlugin):
                logger.warning(f"Plugin {ep.name} does not implement TUIPlugin protocol.")
                continue

            plugins.append(plugin_instance)
            logger.info(f"Loaded plugin: {ep.name}")
        except Exception as e:
            logger.error(f"Failed to load plugin {ep.name}: {e}")

    return plugins
