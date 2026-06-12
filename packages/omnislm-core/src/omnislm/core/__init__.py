"""
OmniSLM Core — Interfaces, contracts, types, and abstractions.

This package contains ZERO business logic and ZERO infrastructure dependencies.
It defines the contracts that all other OmniSLM packages implement.
"""

from omnislm.core.interfaces.runtime import BaseRuntime
from omnislm.core.interfaces.memory import BaseMemory, BaseSessionMemory, BaseSemanticMemory
from omnislm.core.interfaces.agent import BaseAgent, BasePlanner, BaseExecutor
from omnislm.core.interfaces.tool import BaseTool, tool
from omnislm.core.interfaces.embedder import BaseEmbedder
from omnislm.core.interfaces.plugin import BasePlugin
from omnislm.core.interfaces.rag import (
    BaseLoader,
    BaseChunker,
    BaseRetriever,
    BaseReranker,
    BaseVectorStore,
)
from omnislm.core.interfaces.workflow import BaseWorkflow, BaseNode
from omnislm.core.types import (
    ChatMessage,
    CompletionChunk,
    ModelInfo,
    MessageRole,
    ModelRuntime,
    ModelStatus,
    FinishReason,
)
from omnislm.core.exceptions import OmniSLMError
from omnislm.core.events.bus import EventBus
from omnislm.core.events.models import DomainEvent
from omnislm.core.registry import Registry
from omnislm.core.config import OmniSLMConfig
from omnislm.core.container import Container

__all__ = [
    # Interfaces
    "BaseRuntime",
    "BaseMemory",
    "BaseSessionMemory",
    "BaseSemanticMemory",
    "BaseAgent",
    "BasePlanner",
    "BaseExecutor",
    "BaseTool",
    "tool",
    "BaseEmbedder",
    "BasePlugin",
    "BaseLoader",
    "BaseChunker",
    "BaseRetriever",
    "BaseReranker",
    "BaseVectorStore",
    "BaseWorkflow",
    "BaseNode",
    # Types
    "ChatMessage",
    "CompletionChunk",
    "ModelInfo",
    "MessageRole",
    "ModelRuntime",
    "ModelStatus",
    "FinishReason",
    # Events
    "EventBus",
    "DomainEvent",
    # Foundation
    "OmniSLMError",
    "Registry",
    "OmniSLMConfig",
    "Container",
]
