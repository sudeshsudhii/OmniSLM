"""
OmniSLM ReAct Agent.

Implements the Reason + Act (ReAct) loop for autonomous tool use.
Iteratively reasons about a problem, selects tools, observes results,
and generates a final answer.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from omnislm.core.interfaces.agent import BaseAgent
from omnislm.core.interfaces.runtime import BaseRuntime
from omnislm.core.interfaces.tool import BaseTool
from omnislm.core.types import ToolCall, ToolResult

logger = logging.getLogger(__name__)


class ReActAgent(BaseAgent):
    """Agent implementing the ReAct (Reason + Act) loop.

    At each step:
    1. Thought — the model reasons about what to do
    2. Action — the model selects a tool and input
    3. Observation — the tool result is appended
    4. Repeat until Final Answer

    Example:
        agent = ReActAgent(
            name="research_agent",
            description="Answers questions using available tools",
            runtime=ollama_runtime,
            model="qwen2.5:7b",
            tools=[calculator, web_search],
        )
        answer = await agent.run("What is 42 * 17?")
    """

    def __init__(
        self,
        *,
        name: str,
        description: str,
        runtime: BaseRuntime,
        model: str,
        tools: list[BaseTool] | None = None,
    ) -> None:
        self._name = name
        self._description = description
        self._runtime = runtime
        self._model = model
        self._tools = {t.name: t for t in (tools or [])}

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def run(
        self,
        prompt: str,
        *,
        max_iterations: int = 10,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Run the full ReAct loop."""
        tools_desc = "\n".join(
            f"- {name}: {tool.description}" for name, tool in self._tools.items()
        )

        system_prompt = f"""You are a helpful AI assistant. You have access to the following tools:
{tools_desc}

Use the following format EXACTLY:

Thought: <your reasoning about what to do>
Action: <tool name>
Action Input: <input to the tool>

When you observe the result, continue with:
Thought: <reasoning about the observation>

When you have the final answer:
Thought: I now know the final answer
Final Answer: <your final answer>

IMPORTANT: Always start with a Thought. Use tools when needed. End with "Final Answer:".
"""

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        for iteration in range(max_iterations):
            logger.debug("ReAct iteration %d/%d", iteration + 1, max_iterations)

            response = await self._runtime.chat(
                model=self._model,
                messages=messages,
                temperature=0.1,
                max_tokens=1024,
            )

            content = response.get("message", {}).get("content", "")
            messages.append({"role": "assistant", "content": content})

            # Check for Final Answer
            if "Final Answer:" in content:
                final = content.split("Final Answer:")[-1].strip()
                logger.info(
                    "Agent '%s' completed in %d iterations",
                    self._name,
                    iteration + 1,
                )
                return final

            # Parse tool call
            tool_name, tool_input = self._parse_action(content)
            if tool_name and tool_name in self._tools:
                tool = self._tools[tool_name]
                try:
                    result = await tool.execute(
                        **self._parse_tool_input(tool_input)
                    )
                    observation = f"Observation: {result}"
                except Exception as e:
                    observation = f"Observation: Error executing {tool_name}: {e}"

                messages.append({"role": "user", "content": observation})
            else:
                # No valid action — ask the model to try again
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Observation: No valid tool was called. "
                            "Please either use a tool or provide Final Answer."
                        ),
                    }
                )

        return "I was unable to complete the task within the iteration limit."

    async def run_with_tools(
        self,
        prompt: str,
        tool_calls: list[ToolCall],
    ) -> list[ToolResult]:
        """Execute a list of tool calls."""
        results = []
        for tc in tool_calls:
            if tc.name in self._tools:
                try:
                    result = await self._tools[tc.name].execute(**tc.arguments)
                    results.append(
                        ToolResult(
                            tool_call_id=tc.id,
                            name=tc.name,
                            result=result,
                            success=True,
                        )
                    )
                except Exception as e:
                    results.append(
                        ToolResult(
                            tool_call_id=tc.id,
                            name=tc.name,
                            error=str(e),
                            success=False,
                        )
                    )
            else:
                results.append(
                    ToolResult(
                        tool_call_id=tc.id,
                        name=tc.name,
                        error=f"Tool '{tc.name}' not found",
                        success=False,
                    )
                )
        return results

    # ---- Helpers ----

    @staticmethod
    def _parse_action(content: str) -> tuple[str | None, str | None]:
        """Extract Action and Action Input from model output."""
        action = None
        action_input = None

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("Action:"):
                action = line[len("Action:"):].strip()
            elif line.startswith("Action Input:"):
                action_input = line[len("Action Input:"):].strip()

        return action, action_input

    @staticmethod
    def _parse_tool_input(raw_input: str | None) -> dict[str, Any]:
        """Parse tool input into kwargs."""
        if not raw_input:
            return {}
        try:
            return json.loads(raw_input)
        except json.JSONDecodeError:
            # If not JSON, treat as a single positional argument
            return {"expression": raw_input}
