"""
OmniSLM ReAct Agent Implementation.

Reason and Act (ReAct) loop for autonomous tool use.
"""

import json
from typing import Any

from src.core.interfaces.agent import BaseAgent, BaseExecutor, BasePlanner
from src.core.interfaces.runtime import BaseRuntime
from src.core.interfaces.tool import BaseTool


class ReActPlanner(BasePlanner):
    """Generates the next reasoning step or tool to call."""
    
    def __init__(self, runtime: BaseRuntime, model: str):
        self.runtime = runtime
        self.model = model

    async def create_plan(self, task: str) -> list[str]:
        # For pure ReAct, the plan is dynamic, generated one step at a time.
        # This is a stub implementation.
        return ["Analyze Task", "Select Tool", "Execute Tool", "Evaluate Result"]


class ReActExecutor(BaseExecutor):
    """Executes a single step in the ReAct loop."""

    def __init__(self, tools: list[BaseTool]):
        self.tools = {tool.name: tool for tool in tools}

    async def execute_step(self, step: str, context: dict[str, Any]) -> str:
        """Execute a tool if specified in the context."""
        tool_name = context.get("tool")
        tool_input = context.get("tool_input")
        
        if not tool_name or tool_name not in self.tools:
            return "Error: No valid tool specified."
            
        tool = self.tools[tool_name]
        try:
            # Parse input if it's a JSON string
            if isinstance(tool_input, str):
                try:
                    kwargs = json.loads(tool_input)
                except json.JSONDecodeError:
                    # Assume simple string input if not JSON
                    kwargs = {"query": tool_input} if "search" in tool_name else {"expression": tool_input}
            else:
                kwargs = tool_input or {}
                
            result = await tool.execute(**kwargs)
            return str(result)
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"


class ReActAgent(BaseAgent):
    """Agent that uses the ReAct loop to solve tasks."""

    def __init__(
        self,
        name: str,
        description: str,
        runtime: BaseRuntime,
        model: str,
        tools: list[BaseTool]
    ):
        self.name = name
        self.description = description
        self.runtime = runtime
        self.model = model
        self.tools = tools
        self.planner = ReActPlanner(runtime, model)
        self.executor = ReActExecutor(tools)

    async def run(self, prompt: str) -> str:
        """Run the ReAct loop.
        
        In a full implementation, this loops:
        Thought -> Action -> Observation -> Thought -> Final Answer.
        For this MVP, we simulate a single loop.
        """
        # 1. Provide tools context to the LLM
        tools_desc = "\n".join(
            [f"- {t.name}: {t.description}" for t in self.tools]
        )
        
        system_prompt = f"""You are a helpful AI assistant. You have access to the following tools:
{tools_desc}

Use the following format:
Thought: think about what to do
Action: the tool name
Action Input: the input to the tool
Observation: the result of the tool
... (this Thought/Action/Observation can repeat N times)
Thought: I know the final answer
Final Answer: the final answer to the original input question.
"""
        
        # In a real implementation, we would loop this until Final Answer is produced.
        # This is a simplified single-step flow for the framework scaffolding.
        
        # Mock step to show structure
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.runtime.chat(
            model=self.model,
            messages=messages,
            temperature=0.1
        )
        
        return response.get("message", {}).get("content", "Error: No response generated.")
