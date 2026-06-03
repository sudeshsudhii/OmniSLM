"""
OmniSLM Tool Registry.

Manages registration and retrieval of tools/plugins.
"""

from typing import Type

from src.core.exceptions import OmniSLMError
from src.core.interfaces.tool import BaseTool


class ToolRegistryError(OmniSLMError):
    def __init__(self, message: str):
        super().__init__(message=message, code="TOOL_REGISTRY_ERROR")


class ToolRegistry:
    """Registry for dynamically loading and managing tools."""

    def __init__(self):
        self._tools: dict[str, Type[BaseTool]] = {}
        self._instances: dict[str, BaseTool] = {}

    def register(self, tool_class: Type[BaseTool]) -> None:
        """Register a new tool class."""
        # Instantiate temporarily to get name, or class could have it
        instance = tool_class()
        self._tools[instance.name] = tool_class
        self._instances[instance.name] = instance

    def get_tool(self, name: str) -> BaseTool:
        """Get a tool instance by name."""
        if name not in self._instances:
            raise ToolRegistryError(f"Tool '{name}' not registered")
        return self._instances[name]

    def list_tools(self) -> list[dict[str, str]]:
        """List all registered tools."""
        return [
            {"name": name, "description": instance.description}
            for name, instance in self._instances.items()
        ]


# Global tool registry
tool_registry = ToolRegistry()
