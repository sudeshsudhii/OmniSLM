"""
OmniSLM Plugin Lifecycle Manager.

Handles initialize → active → shutdown transitions.
"""

from __future__ import annotations

import logging
from typing import Any

from omnislm.core.interfaces.plugin import BasePlugin
from omnislm.plugins.discovery import PluginDiscovery
from omnislm.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginLifecycleManager:
    """Manages the full lifecycle of plugins."""

    def __init__(self) -> None:
        self.registry = PluginRegistry()
        self.discovery = PluginDiscovery()

    async def install(self, name: str, config: dict[str, Any] | None = None) -> BasePlugin | None:
        """Discover, load, initialize, and register a plugin."""
        plugin = self.discovery.load_plugin(name)
        if not plugin:
            logger.error("Plugin '%s' not found", name)
            return None

        try:
            await plugin.initialize(config or {})
            self.registry.register(plugin)
            logger.info("Plugin '%s' v%s installed and active", plugin.name, plugin.version)
            return plugin
        except Exception as e:
            logger.error("Failed to initialize plugin '%s': %s", name, e)
            return None

    async def uninstall(self, name: str) -> None:
        """Shutdown and remove a plugin."""
        try:
            plugin = self.registry.get(name)
            await plugin.shutdown()
        except Exception as e:
            logger.error("Error shutting down plugin '%s': %s", name, e)

    async def shutdown_all(self) -> None:
        """Shutdown all active plugins."""
        for name in self.registry.list_active():
            try:
                plugin = self.registry.get(name)
                await plugin.shutdown()
            except Exception as e:
                logger.error("Error shutting down plugin '%s': %s", name, e)
