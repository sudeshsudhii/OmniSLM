"""
OmniSLM Agent SDK Interfaces.

Contracts for building autonomous agents.
"""

from abc import ABC, abstractmethod
from typing import Any

from src.core.interfaces.runtime import BaseRuntime
from src.core.interfaces.tool import BaseTool


class BasePlanner(ABC):
    """Abstract base class for agent planners."""
    
    @abstractmethod
    async def create_plan(self, task: str) -> list[str]:
        """Generate a sequence of steps to solve the task."""
        pass


class BaseExecutor(ABC):
    """Abstract base class for step executors."""
    
    @abstractmethod
    async def execute_step(self, step: str, context: dict[str, Any]) -> str:
        """Execute a single step and return the result."""
        pass


class BaseAgent(ABC):
    """Abstract base class for an autonomous agent."""
    
    name: str
    description: str
    runtime: BaseRuntime
    tools: list[BaseTool]

    @abstractmethod
    async def run(self, prompt: str) -> str:
        """Run the agent on a specific prompt/task."""
        pass
