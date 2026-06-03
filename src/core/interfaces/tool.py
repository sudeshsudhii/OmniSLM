"""
OmniSLM Tool Interface.

Defines the contract for Agent Tools / Plugins.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Type


class BaseTool(ABC):
    """Abstract base class for all tools/plugins."""
    
    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool logic."""
        pass


def tool(name: str, description: str) -> Callable:
    """Decorator to easily convert a function into a BaseTool."""
    def decorator(func: Callable) -> Type[BaseTool]:
        class FuncTool(BaseTool):
            def __init__(self):
                self.name = name
                self.description = description
                self.func = func

            async def execute(self, **kwargs: Any) -> Any:
                import inspect
                if inspect.iscoroutinefunction(self.func):
                    return await self.func(**kwargs)
                return self.func(**kwargs)
        
        return FuncTool
    return decorator
