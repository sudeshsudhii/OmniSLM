"""
OmniSLM Workflow Nodes.

Built-in node types for common workflow operations.
"""

from __future__ import annotations

from typing import Any, Callable

from omnislm.core.interfaces.runtime import BaseRuntime
from omnislm.core.interfaces.tool import BaseTool
from omnislm.core.interfaces.workflow import BaseNode
from omnislm.core.types import WorkflowState


class LLMNode(BaseNode):
    """A node that calls an LLM for generation."""

    def __init__(
        self,
        node_id: str,
        runtime: BaseRuntime,
        model: str,
        prompt_template: str,
        *,
        output_key: str = "llm_output",
        temperature: float = 0.7,
        dependencies: list[str] | None = None,
    ) -> None:
        self._node_id = node_id
        self._runtime = runtime
        self._model = model
        self._prompt_template = prompt_template
        self._output_key = output_key
        self._temperature = temperature
        self._dependencies = dependencies or []

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def node_type(self) -> str:
        return "llm"

    def get_dependencies(self) -> list[str]:
        return self._dependencies

    async def execute(self, state: WorkflowState) -> WorkflowState:
        prompt = self._prompt_template.format(**state.data)
        response = await self._runtime.generate(
            model=self._model,
            prompt=prompt,
            temperature=self._temperature,
        )
        state.set(self._output_key, response.get("response", ""))
        return state


class ToolNode(BaseNode):
    """A node that executes a tool."""

    def __init__(
        self,
        node_id: str,
        tool: BaseTool,
        *,
        input_mapping: dict[str, str] | None = None,
        output_key: str = "tool_output",
        dependencies: list[str] | None = None,
    ) -> None:
        self._node_id = node_id
        self._tool = tool
        self._input_mapping = input_mapping or {}
        self._output_key = output_key
        self._dependencies = dependencies or []

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def node_type(self) -> str:
        return "tool"

    def get_dependencies(self) -> list[str]:
        return self._dependencies

    async def execute(self, state: WorkflowState) -> WorkflowState:
        kwargs = {}
        for tool_param, state_key in self._input_mapping.items():
            kwargs[tool_param] = state.get(state_key)

        result = await self._tool.execute(**kwargs)
        state.set(self._output_key, result)
        return state


class TransformNode(BaseNode):
    """A node that transforms state using a custom function."""

    def __init__(
        self,
        node_id: str,
        transform_fn: Callable[[WorkflowState], WorkflowState],
        *,
        dependencies: list[str] | None = None,
    ) -> None:
        self._node_id = node_id
        self._transform_fn = transform_fn
        self._dependencies = dependencies or []

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def node_type(self) -> str:
        return "transform"

    def get_dependencies(self) -> list[str]:
        return self._dependencies

    async def execute(self, state: WorkflowState) -> WorkflowState:
        import inspect

        if inspect.iscoroutinefunction(self._transform_fn):
            return await self._transform_fn(state)
        return self._transform_fn(state)
