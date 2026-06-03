"""
OmniSLM Core Interfaces.
"""

from src.core.interfaces.agent import BaseAgent, BaseExecutor, BasePlanner
from src.core.interfaces.embedder import BaseEmbedder
from src.core.interfaces.memory import BaseMemory
from src.core.interfaces.runtime import BaseRuntime
from src.core.interfaces.tool import BaseTool, tool

__all__ = [
    "BaseRuntime",
    "BaseEmbedder",
    "BaseMemory",
    "BaseTool",
    "tool",
    "BaseAgent",
    "BaseExecutor",
    "BasePlanner",
]
