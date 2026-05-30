"""
OmniSLM Core Domain Types & Enums.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"


class MessageRole(str, enum.Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ModelRuntime(str, enum.Enum):
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    VLLM = "vllm"
    HUGGINGFACE = "huggingface"


class ModelStatus(str, enum.Enum):
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class FinishReason(str, enum.Enum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    ERROR = "error"


# ---- Value Objects ----

@dataclass(frozen=True)
class AuthContext:
    """Immutable authentication context passed through the request lifecycle."""

    user_id: UUID
    tenant_id: UUID
    email: str
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TokenPair:
    """JWT access + refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


@dataclass
class ChatMessage:
    """A single message in a conversation."""

    role: MessageRole
    content: str
    name: str | None = None


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
