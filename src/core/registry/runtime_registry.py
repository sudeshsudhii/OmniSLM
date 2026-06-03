"""
OmniSLM Runtime Registry.

Manages instantiation and retrieval of LLM inference runtimes.
"""

from typing import Type

from src.core.exceptions import OmniSLMError
from src.core.interfaces.runtime import BaseRuntime
from src.core.types import ModelRuntime


class RuntimeRegistryError(OmniSLMError):
    def __init__(self, message: str):
        super().__init__(message=message, code="RUNTIME_REGISTRY_ERROR")


class RuntimeRegistry:
    """Registry for dynamically loading and managing runtimes."""

    def __init__(self):
        self._runtimes: dict[str, Type[BaseRuntime]] = {}
        self._instances: dict[str, BaseRuntime] = {}

    def register(self, name: str, runtime_class: Type[BaseRuntime]) -> None:
        """Register a new runtime class."""
        self._runtimes[name] = runtime_class

    def get_runtime(self, name: str, **kwargs) -> BaseRuntime:
        """Get or create a runtime instance."""
        if name not in self._runtimes:
            raise RuntimeRegistryError(f"Runtime '{name}' not registered")

        if name not in self._instances:
            self._instances[name] = self._runtimes[name](**kwargs)

        return self._instances[name]

    async def close_all(self) -> None:
        """Close all instantiated runtimes."""
        for name, instance in self._instances.items():
            try:
                await instance.close()
            except Exception:
                pass
        self._instances.clear()


# Global registry instance
runtime_registry = RuntimeRegistry()
