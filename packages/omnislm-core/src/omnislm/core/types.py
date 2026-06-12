"""
OmniSLM Core Domain Types & Enums.

Framework-level value objects and enumerations used across all packages.
These types are stable and should rarely change.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


# ============================================================
#  Enumerations
# ============================================================


class MessageRole(str, enum.Enum):
    """Role of a message in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ModelRuntime(str, enum.Enum):
    """Supported LLM inference runtimes."""
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    VLLM = "vllm"
    TRANSFORMERS = "transformers"
    ONNX = "onnx"


class ModelStatus(str, enum.Enum):
    """Status of a model within a runtime."""
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class FinishReason(str, enum.Enum):
    """Reason a model stopped generating."""
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    ERROR = "error"


class PluginStatus(str, enum.Enum):
    """Lifecycle status of a plugin."""
    DISCOVERED = "discovered"
    INSTALLED = "installed"
    CONFIGURED = "configured"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class MemoryTier(str, enum.Enum):
    """Tiers of the memory subsystem."""
    SESSION = "session"
    CONVERSATION = "conversation"
    SEMANTIC = "semantic"
    LONG_TERM = "long_term"
    USER = "user"


# ============================================================
#  Value Objects
# ============================================================


@dataclass
class ChatMessage:
    """A single message in a conversation."""
    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


@dataclass
class ModelInfo:
    """Information about an available model."""
    id: str
    name: str
    family: str
    parameters: str | None = None
    quantization: str | None = None
    runtime: ModelRuntime = ModelRuntime.OLLAMA
    context_length: int = 4096
    capabilities: list[str] = field(default_factory=list)
    status: ModelStatus = ModelStatus.AVAILABLE
    size_bytes: int | None = None


@dataclass
class CompletionChunk:
    """A single chunk of a streaming completion."""
    id: str
    content: str
    model: str
    finish_reason: FinishReason | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class ToolCall:
    """A tool/function call requested by the model."""
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Result of executing a tool call."""
    tool_call_id: str
    name: str
    result: Any = None
    error: str | None = None
    success: bool = True


@dataclass(frozen=True)
class PluginManifest:
    """Metadata describing a plugin."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = ""
    entry_point: str = ""
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """A loaded document with text content and metadata."""
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def source(self) -> str | None:
        return self.metadata.get("source")


@dataclass
class Chunk:
    """A chunk of a document after splitting."""
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

    @property
    def source(self) -> str | None:
        return self.metadata.get("source")

    @property
    def chunk_index(self) -> int:
        return self.metadata.get("chunk_index", 0)


@dataclass
class RetrievalResult:
    """A single result from a retriever."""
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str | None = None


@dataclass
class WorkflowState:
    """State passed between nodes in a workflow."""
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    completed_nodes: list[str] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
