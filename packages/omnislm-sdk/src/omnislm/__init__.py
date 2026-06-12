"""
OmniSLM — The open-source AI framework for Small Language Models.

Build AI assistants, RAG applications, and autonomous agents
using local or self-hosted models.

Quick Start:
    from omnislm import OmniSLM

    app = OmniSLM()
    app.enable_memory()
    app.enable_rag()
    app.enable_agents()
    app.run()
"""

from omnislm.app import OmniSLM

# Re-export core types for convenience
from omnislm.core import (
    BaseRuntime,
    BaseMemory,
    BaseAgent,
    BaseTool,
    BasePlugin,
    BaseEmbedder,
    BaseLoader,
    BaseChunker,
    BaseRetriever,
    BaseReranker,
    BaseVectorStore,
    BaseWorkflow,
    BaseNode,
    OmniSLMConfig,
    EventBus,
    DomainEvent,
    Registry,
    Container,
    OmniSLMError,
    tool,
    ChatMessage,
    CompletionChunk,
    ModelInfo,
    MessageRole,
)

__version__ = "0.1.0"

__all__ = [
    "OmniSLM",
    # Interfaces
    "BaseRuntime",
    "BaseMemory",
    "BaseAgent",
    "BaseTool",
    "BasePlugin",
    "BaseEmbedder",
    "BaseLoader",
    "BaseChunker",
    "BaseRetriever",
    "BaseReranker",
    "BaseVectorStore",
    "BaseWorkflow",
    "BaseNode",
    # Framework
    "OmniSLMConfig",
    "EventBus",
    "DomainEvent",
    "Registry",
    "Container",
    "OmniSLMError",
    "tool",
    # Types
    "ChatMessage",
    "CompletionChunk",
    "ModelInfo",
    "MessageRole",
]
