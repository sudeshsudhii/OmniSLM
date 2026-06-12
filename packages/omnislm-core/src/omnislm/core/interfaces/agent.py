"""
OmniSLM Agent SDK Interfaces.

Contracts for building autonomous agents with planning and execution.
"""

from abc import ABC, abstractmethod
from typing import Any

from omnislm.core.types import ToolCall, ToolResult


class BasePlanner(ABC):
    """Abstract base class for agent planners.

    A planner takes a task description and produces a plan
    (sequence of steps or tool calls).
    """

    @abstractmethod
    async def create_plan(self, task: str, context: dict[str, Any] | None = None) -> list[str]:
        """Generate a sequence of steps to solve the task."""

    @abstractmethod
    async def replan(
        self,
        task: str,
        completed_steps: list[str],
        observations: list[str],
    ) -> list[str]:
        """Re-plan based on completed steps and observations."""


class BaseExecutor(ABC):
    """Abstract base class for step executors.

    An executor takes a step description and context, then performs the action.
    """

    @abstractmethod
    async def execute_step(
        self, step: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a single step and return the result.

        Returns:
            Dict with 'output', 'tool_calls' (if any), 'finished' keys.
        """


class BaseAgent(ABC):
    """Abstract base class for an autonomous agent.

    Agents combine a planner, executor, tools, and a runtime
    to autonomously solve tasks.

    Example:
        class MyAgent(BaseAgent):
            async def run(self, prompt):
                plan = await self.planner.create_plan(prompt)
                for step in plan:
                    result = await self.executor.execute_step(step, {})
                return result
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent's unique name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the agent's purpose."""

    @abstractmethod
    async def run(
        self,
        prompt: str,
        *,
        max_iterations: int = 10,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Run the agent on a specific prompt/task.

        Args:
            prompt: The task or question to solve.
            max_iterations: Maximum number of reasoning steps.
            context: Optional context dict (previous results, memory, etc.).

        Returns:
            The agent's final answer as a string.
        """

    @abstractmethod
    async def run_with_tools(
        self,
        prompt: str,
        tool_calls: list[ToolCall],
    ) -> list[ToolResult]:
        """Execute a list of tool calls and return results."""
