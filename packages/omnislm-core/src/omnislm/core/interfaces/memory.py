"""
OmniSLM Memory Interfaces.

Contracts for the multi-tier memory subsystem:
- BaseMemory: generic memory store
- BaseSessionMemory: short-term, per-session (Redis-backed)
- BaseSemanticMemory: vector-backed semantic recall
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseMemory(ABC):
    """Abstract base class for all memory engines."""

    @property
    @abstractmethod
    def tier(self) -> str:
        """Memory tier identifier (session, conversation, semantic, long_term, user)."""

    @abstractmethod
    async def add(self, session_id: str, content: str, role: str, **metadata: Any) -> None:
        """Add a new memory entry."""

    @abstractmethod
    async def recall(
        self, session_id: str, query: str, *, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Retrieve relevant memories for the given query.

        Returns:
            List of dicts with at least 'content' and 'role' keys,
            plus any additional metadata.
        """

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        """Clear all memories for a session."""


class BaseSessionMemory(BaseMemory):
    """Short-term session memory — typically backed by Redis or in-memory store.

    Stores the last N messages and retrieves them in FIFO order.
    """

    @property
    def tier(self) -> str:
        return "session"

    @abstractmethod
    async def get_recent(
        self, session_id: str, *, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get the most recent messages in FIFO order."""

    @abstractmethod
    async def set_ttl(self, session_id: str, ttl_seconds: int) -> None:
        """Set time-to-live for a session's memory."""


class BaseSemanticMemory(BaseMemory):
    """Vector-backed semantic memory — uses embeddings for retrieval.

    Stores memories as vectors and retrieves them based on cosine similarity.
    """

    @property
    def tier(self) -> str:
        return "semantic"

    @abstractmethod
    async def search(
        self,
        session_id: str,
        query_vector: list[float],
        *,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Search memories by vector similarity."""
