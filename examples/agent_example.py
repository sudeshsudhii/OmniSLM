"""
OmniSLM Agent Example.

Demonstrates creating a ReAct agent with tools.

Usage:
    pip install omnislm[agents]
    python agent_example.py
"""

import asyncio
from omnislm.agents import ReActAgent
from omnislm.runtimes import OllamaRuntime
from omnislm.plugins.builtins.calculator import CalculatorTool
from omnislm.plugins.builtins.datetime_plugin import DateTimeTool


async def main():
    """Run an agent with tools."""
    
    # 1. Setup runtime
    runtime = OllamaRuntime(base_url="http://localhost:11434")
    await runtime.initialize()
    
    # 2. Create tools
    tools = [CalculatorTool(), DateTimeTool()]
    
    # 3. Create agent
    agent = ReActAgent(
        name="math_agent",
        description="An agent that can do math and tell time",
        runtime=runtime,
        model="qwen2.5:7b",
        tools=tools,
    )
    
    # 4. Run the agent
    print("🤖 Running agent...")
    answer = await agent.run("What is 42 * 17 + 99?")
    print(f"Answer: {answer}")
    
    await runtime.close()


if __name__ == "__main__":
    asyncio.run(main())
