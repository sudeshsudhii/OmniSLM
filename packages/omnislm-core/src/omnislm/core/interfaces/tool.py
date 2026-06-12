"""
OmniSLM Tool Interface.

Defines the contract for Agent Tools and the @tool decorator
for converting functions into tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Type
import inspect


class BaseTool(ABC):
    """Abstract base class for all tools.

    Tools are capabilities that agents can invoke to interact
    with external systems (calculators, APIs, databases, etc.).

    Example:
        class WeatherTool(BaseTool):
            name = "weather"
            description = "Get current weather for a location"

            async def execute(self, location: str) -> str:
                return f"Sunny in {location}"
    """

    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool logic with the given arguments."""

    def get_schema(self) -> dict[str, Any]:
        """Return a JSON Schema describing the tool's parameters.

        Override this for richer schema support. The default
        implementation introspects the execute method's signature.
        """
        sig = inspect.signature(self.execute)
        properties = {}
        required = []
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "kwargs"):
                continue
            prop: dict[str, Any] = {"type": "string"}
            if param.annotation != inspect.Parameter.empty:
                type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}
                prop["type"] = type_map.get(param.annotation, "string")
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            properties[param_name] = prop

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


def tool(name: str, description: str) -> Callable:
    """Decorator to convert a function into a BaseTool.

    Example:
        @tool(name="calculator", description="Evaluate math expressions")
        async def calc(expression: str) -> str:
            return str(eval(expression))
    """

    def decorator(func: Callable) -> Type[BaseTool]:
        class FuncTool(BaseTool):
            def __init__(self) -> None:
                self.name = name
                self.description = description
                self._func = func

            async def execute(self, **kwargs: Any) -> Any:
                if inspect.iscoroutinefunction(self._func):
                    return await self._func(**kwargs)
                return self._func(**kwargs)

        FuncTool.__name__ = f"{name}_tool"
        FuncTool.__qualname__ = f"{name}_tool"
        return FuncTool

    return decorator
