"""
OmniSLM Generic Registry.

A type-safe, instance-based registry pattern for managing
runtimes, tools, plugins, and other components.

No global singletons — each OmniSLM app creates its own registries.
"""

from __future__ import annotations

import logging
from typing import Any, Generic, Type, TypeVar

from omnislm.core.exceptions import RegistryError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Registry(Generic[T]):
    """Generic registry for managing typed components.

    Supports registering classes (lazy instantiation) or instances (eager).

    Example:
        registry = Registry[BaseRuntime]("runtime")
        registry.register("ollama", OllamaRuntime)
        runtime = registry.get("ollama", base_url="http://localhost:11434")

        # Or register an instance directly
        registry.register_instance("custom", my_runtime_instance)
    """

    def __init__(self, name: str = "component") -> None:
        """Initialize the registry.

        Args:
            name: Human-readable name for error messages (e.g., 'runtime', 'plugin').
        """
        self._name = name
        self._classes: dict[str, Type[T]] = {}
        self._instances: dict[str, T] = {}

    def register(self, key: str, cls: Type[T]) -> None:
        """Register a class for lazy instantiation.

        Args:
            key: Unique identifier for the component.
            cls: The class to register.
        """
        self._classes[key] = cls
        logger.debug("Registered %s class: %s", self._name, key)

    def register_instance(self, key: str, instance: T) -> None:
        """Register a pre-created instance.

        Args:
            key: Unique identifier for the component.
            instance: The instance to register.
        """
        self._instances[key] = instance
        logger.debug("Registered %s instance: %s", self._name, key)

    def get(self, key: str, **kwargs: Any) -> T:
        """Get or create a component instance.

        If an instance exists, return it. Otherwise, create one
        from the registered class with the given kwargs.

        Args:
            key: The component identifier.
            **kwargs: Arguments passed to the class constructor (if creating).

        Returns:
            The component instance.

        Raises:
            RegistryError: If the key is not registered.
        """
        if key in self._instances:
            return self._instances[key]

        if key not in self._classes:
            available = ", ".join(self.list_registered())
            raise RegistryError(
                f"{self._name.title()} '{key}' not registered. "
                f"Available: [{available}]"
            )

        instance = self._classes[key](**kwargs)
        self._instances[key] = instance
        return instance

    def has(self, key: str) -> bool:
        """Check if a key is registered (class or instance)."""
        return key in self._classes or key in self._instances

    def list_registered(self) -> list[str]:
        """List all registered keys."""
        return sorted(set(self._classes.keys()) | set(self._instances.keys()))

    def list_instances(self) -> dict[str, T]:
        """Return all instantiated components."""
        return dict(self._instances)

    async def close_all(self) -> None:
        """Close all instantiated components that have a close() method."""
        for key, instance in self._instances.items():
            if hasattr(instance, "close"):
                try:
                    close_result = instance.close()  # type: ignore
                    if hasattr(close_result, "__await__"):
                        await close_result
                except Exception as e:
                    logger.error(
                        "Error closing %s '%s': %s", self._name, key, str(e)
                    )
        self._instances.clear()

    def clear(self) -> None:
        """Remove all registrations."""
        self._classes.clear()
        self._instances.clear()

    def __len__(self) -> int:
        return len(set(self._classes.keys()) | set(self._instances.keys()))

    def __contains__(self, key: str) -> bool:
        return self.has(key)
