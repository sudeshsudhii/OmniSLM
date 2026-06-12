"""
OmniSLM Plugin Discovery.

Discovers plugins via Python entry_points and local directories.
"""

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from omnislm.core.interfaces.plugin import BasePlugin

logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Discovers and loads OmniSLM plugins."""

    ENTRY_POINT_GROUP = "omnislm.plugins"

    def discover_installed(self) -> dict[str, type[BasePlugin]]:
        """Find all plugins installed via pip (entry_points)."""
        plugins: dict[str, type[BasePlugin]] = {}

        try:
            eps = entry_points(group=self.ENTRY_POINT_GROUP)
            for ep in eps:
                try:
                    cls = ep.load()
                    plugins[ep.name] = cls
                    logger.info("Discovered plugin: %s", ep.name)
                except Exception as e:
                    logger.warning("Failed to load plugin '%s': %s", ep.name, e)
        except Exception as e:
            logger.debug("No entry_points found for group '%s': %s", self.ENTRY_POINT_GROUP, e)

        return plugins

    def load_plugin(self, name: str, **config: Any) -> BasePlugin | None:
        """Load a specific plugin by name."""
        plugins = self.discover_installed()

        if name in plugins:
            cls = plugins[name]
            return cls()

        # Check builtin plugins
        builtins = self._get_builtins()
        if name in builtins:
            return builtins[name]()

        return None

    def _get_builtins(self) -> dict[str, type[BasePlugin]]:
        """Return built-in plugins."""
        from omnislm.plugins.builtins.calculator import CalculatorPlugin
        from omnislm.plugins.builtins.datetime_plugin import DateTimePlugin

        return {
            "calculator": CalculatorPlugin,
            "datetime": DateTimePlugin,
        }
