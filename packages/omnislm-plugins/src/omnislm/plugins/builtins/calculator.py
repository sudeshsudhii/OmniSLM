"""
Built-in Calculator Plugin.

Provides a safe mathematical expression evaluator.
"""

import ast
import operator
from typing import Any

from omnislm.core.interfaces.plugin import BasePlugin
from omnislm.core.interfaces.tool import BaseTool

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


class CalculatorTool(BaseTool):
    """Safe math expression evaluator."""

    name = "calculator"
    description = (
        "Evaluate mathematical expressions. "
        "Input should be a math expression like '2 + 2'."
    )

    async def execute(self, expression: str = "") -> str:
        try:
            def _eval(node: ast.AST) -> Any:
                if isinstance(node, ast.Constant):
                    return node.value
                elif isinstance(node, ast.BinOp):
                    return _ALLOWED_OPS[type(node.op)](
                        _eval(node.left), _eval(node.right)
                    )
                elif isinstance(node, ast.UnaryOp):
                    return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
                else:
                    raise TypeError(f"Unsupported: {type(node)}")

            tree = ast.parse(expression, mode="eval").body
            return str(_eval(tree))
        except Exception as e:
            return f"Error: {e}"


class CalculatorPlugin(BasePlugin):
    """Calculator plugin providing math evaluation."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Evaluate mathematical expressions safely"

    async def initialize(self, config: dict[str, Any]) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def get_tools(self) -> list[BaseTool]:
        return [CalculatorTool()]
