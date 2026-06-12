"""
OmniSLM Runtime Manager.

Manages the lifecycle of LLM inference runtimes:
registration, initialization, health checking, and hot-swapping.
"""

from __future__ import annotations

import logging
from typing import Any

from omnislm.core.config import OmniSLMConfig, RuntimeConfig
from omnislm.core.exceptions import RuntimeNotAvailableError
from omnislm.core.interfaces.runtime import BaseRuntime
from omnislm.core.registry import Registry

logger = logging.getLogger(__name__)


class RuntimeManager:
    """Manages LLM runtime instances and their lifecycle.

    Handles registration, initialization, health monitoring,
    and provides access to the default runtime.
    """

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self._config = config or RuntimeConfig()
        self._registry: Registry[BaseRuntime] = Registry("runtime")
        self._default_name: str = self._config.default

    @property
    def default_runtime(self) -> BaseRuntime:
        """Get the default runtime instance."""
        if not self._registry.has(self._default_name):
            raise RuntimeNotAvailableError(self._default_name)
        return self._registry.get(self._default_name)

    def register(self, name: str, runtime: BaseRuntime) -> None:
        """Register a runtime instance."""
        self._registry.register_instance(name, runtime)

    def register_class(self, name: str, cls: type[BaseRuntime]) -> None:
        """Register a runtime class for lazy instantiation."""
        self._registry.register(name, cls)

    def get(self, name: str, **kwargs: Any) -> BaseRuntime:
        """Get a runtime by name."""
        return self._registry.get(name, **kwargs)

    def set_default(self, name: str) -> None:
        """Set the default runtime."""
        self._default_name = name

    async def initialize_all(self) -> None:
        """Initialize all registered runtime instances."""
        for name, runtime in self._registry.list_instances().items():
            try:
                await runtime.initialize()
                logger.info("Runtime '%s' initialized", name)
            except Exception as e:
                logger.error("Failed to initialize runtime '%s': %s", name, e)

    async def health_check(self) -> dict[str, bool]:
        """Check health of all registered runtimes."""
        results = {}
        for name, runtime in self._registry.list_instances().items():
            try:
                results[name] = await runtime.is_available()
            except Exception:
                results[name] = False
        return results

    async def close_all(self) -> None:
        """Close all runtime instances."""
        await self._registry.close_all()

    def list_runtimes(self) -> list[str]:
        """List all registered runtime names."""
        return self._registry.list_registered()

    def auto_register(self, config: RuntimeConfig | None = None) -> None:
        """Auto-register runtimes based on configuration.

        Imports and registers runtime classes for configured backends.
        """
        cfg = config or self._config

        # Always register Ollama (the default)
        from omnislm.runtimes.ollama import OllamaRuntime

        if not self._registry.has("ollama"):
            self._registry.register_instance(
                "ollama", OllamaRuntime(base_url=cfg.ollama_base_url)
            )

        # Register vLLM if configured
        if cfg.vllm_base_url:
            try:
                from omnislm.runtimes.vllm import VLLMRuntime

                if not self._registry.has("vllm"):
                    self._registry.register_instance(
                        "vllm", VLLMRuntime(base_url=cfg.vllm_base_url)
                    )
            except ImportError:
                logger.debug("vLLM runtime not available (missing dependencies)")
