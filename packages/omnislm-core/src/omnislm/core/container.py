"""
OmniSLM Dependency Injection Container.

Manages the lifecycle of all framework components (runtimes, registries,
event bus, memory, etc.) in a centralized, testable container.

No global singletons — each OmniSLM app creates its own Container.
"""

from __future__ import annotations

import logging
from typing import Any

from omnislm.core.config import OmniSLMConfig
from omnislm.core.events.bus import EventBus
from omnislm.core.registry import Registry
from omnislm.core.interfaces.runtime import BaseRuntime
from omnislm.core.interfaces.tool import BaseTool
from omnislm.core.interfaces.plugin import BasePlugin
from omnislm.core.interfaces.memory import BaseMemory
from omnislm.core.interfaces.embedder import BaseEmbedder
from omnislm.core.interfaces.rag import BaseVectorStore

logger = logging.getLogger(__name__)


class Container:
    """Dependency Injection container for the OmniSLM framework.

    Holds all registries, the event bus, and configuration
    in a single, non-global object. Each OmniSLM application
    instance gets its own Container.

    Example:
        container = Container(config)
        container.runtime_registry.register("ollama", OllamaRuntime)
        runtime = container.runtime_registry.get("ollama")
    """

    def __init__(self, config: OmniSLMConfig | None = None) -> None:
        self.config = config or OmniSLMConfig()

        # ---- Event Bus ----
        self.event_bus = EventBus()

        # ---- Registries ----
        self.runtime_registry: Registry[BaseRuntime] = Registry("runtime")
        self.tool_registry: Registry[BaseTool] = Registry("tool")
        self.plugin_registry: Registry[BasePlugin] = Registry("plugin")
        self.memory_registry: Registry[BaseMemory] = Registry("memory")
        self.embedder_registry: Registry[BaseEmbedder] = Registry("embedder")
        self.vector_store_registry: Registry[BaseVectorStore] = Registry("vector_store")

        # ---- State ----
        self._initialized = False
        self._services: dict[str, Any] = {}

    def register_service(self, name: str, service: Any) -> None:
        """Register a custom service in the container.

        Args:
            name: Service identifier.
            service: The service instance.
        """
        self._services[name] = service

    def get_service(self, name: str) -> Any:
        """Get a registered service.

        Args:
            name: Service identifier.

        Returns:
            The service instance.

        Raises:
            KeyError: If the service is not registered.
        """
        if name not in self._services:
            raise KeyError(f"Service '{name}' not registered in container")
        return self._services[name]

    def has_service(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services

    async def initialize(self) -> None:
        """Initialize all registered components.

        Called during application startup to establish connections,
        warm up caches, etc.
        """
        if self._initialized:
            return

        logger.info("Initializing OmniSLM container")

        # Initialize runtime instances
        for key, runtime in self.runtime_registry.list_instances().items():
            try:
                await runtime.initialize()
                logger.info("Runtime '%s' initialized", key)
            except Exception as e:
                logger.error("Failed to initialize runtime '%s': %s", key, e)

        # Initialize plugins
        for key, plugin in self.plugin_registry.list_instances().items():
            try:
                plugin_config = {}
                for pc in self.config.plugins:
                    if pc.name == key:
                        plugin_config = pc.config
                        break
                await plugin.initialize(plugin_config)
                logger.info("Plugin '%s' initialized", key)
            except Exception as e:
                logger.error("Failed to initialize plugin '%s': %s", key, e)

        self._initialized = True
        logger.info("Container initialization complete")

    async def shutdown(self) -> None:
        """Shutdown all components and release resources.

        Called during application shutdown.
        """
        logger.info("Shutting down OmniSLM container")

        # Shutdown plugins (reverse order)
        for key, plugin in reversed(
            list(self.plugin_registry.list_instances().items())
        ):
            try:
                await plugin.shutdown()
            except Exception as e:
                logger.error("Error shutting down plugin '%s': %s", key, e)

        # Close runtimes
        await self.runtime_registry.close_all()

        # Close vector stores
        await self.vector_store_registry.close_all()

        # Clear event bus
        self.event_bus.clear()

        self._initialized = False
        logger.info("Container shutdown complete")
