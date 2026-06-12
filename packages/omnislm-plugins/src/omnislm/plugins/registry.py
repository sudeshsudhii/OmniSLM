"""
OmniSLM Plugin Registry.

Instance-based registry for managing plugin instances.
"""

from __future__ import annotations

import logging
from typing import Any

from omnislm.core.exceptions import PluginNotFoundError
from omnislm.core.interfaces.plugin import BasePlugin
from omnislm.core.registry import Registry

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing OmniSLM plugins.

    Provides higher-level plugin management on top of the generic Registry.
    """

    def __init__(self) -> None:
        self._registry: Registry[BasePlugin] = Registry("plugin")
        self._active: set[str] = set()

    def register(self, plugin: BasePlugin) -> None:
        """Register and mark a plugin as active."""
        self._registry.register_instance(plugin.name, plugin)
        self._active.add(plugin.name)

    def get(self, name: str) -> BasePlugin:
        """Get a plugin by name."""
        if not self._registry.has(name):
            raise PluginNotFoundError(name)
        return self._registry.get(name)

    def is_active(self, name: str) -> bool:
        return name in self._active

    def disable(self, name: str) -> None:
        self._active.discard(name)

    def enable(self, name: str) -> None:
        if self._registry.has(name):
            self._active.add(name)

    def list_all(self) -> list[str]:
        return self._registry.list_registered()

    def list_active(self) -> list[str]:
        return sorted(self._active)

    def get_all_tools(self) -> list[Any]:
        """Collect tools from all active plugins."""
        tools = []
        for name in self._active:
            plugin = self._registry.get(name)
            tools.extend(plugin.get_tools())
        return tools

    def get_all_routes(self) -> list[Any]:
        """Collect routes from all active plugins."""
        routes = []
        for name in self._active:
            plugin = self._registry.get(name)
            routes.extend(plugin.get_routes())
        return routes
