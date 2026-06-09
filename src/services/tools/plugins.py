"""
OmniSLM Default Plugins.

Basic tools registered out of the box.
"""

import ast
import operator
from typing import Any

from src.core.interfaces.tool import tool
from src.core.registry.tool_registry import tool_registry

# Allowed operators for the safe calculator
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


@tool(
    name="calculator",
    description="Evaluate mathematical expressions. Use this tool when you need to perform math. Input should be a mathematical expression string like '2 + 2'."
)
async def calculator_tool(expression: str) -> str:
    """Safely evaluates a math expression."""
    try:
        def _eval(node: ast.AST) -> Any:
            if isinstance(node, ast.Num):  # < python 3.8
                return node.n
            elif isinstance(node, ast.Constant):  # >= python 3.8
                return node.value
            elif isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                op = _ALLOWED_OPERATORS[type(node.op)]
                return op(left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = _eval(node.operand)
                op = _ALLOWED_OPERATORS[type(node.op)]
                return op(operand)
            else:
                raise TypeError(f"Unsupported node type: {type(node)}")

        node = ast.parse(expression, mode='eval').body
        result = _eval(node)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"


@tool(
    name="web_search",
    description="Search the web for current information. Input should be a search query string."
)
async def web_search_tool(query: str) -> str:
    """Stub for a web search tool. Requires an API key (e.g., Tavily, DuckDuckGo)."""
    return f"Simulated web search results for: '{query}'. In a real environment, this would call a search API."


# Register core tools
tool_registry.register(calculator_tool)
tool_registry.register(web_search_tool)
