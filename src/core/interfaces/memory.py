"""
OmniSLM Memory Interfaces.

Contracts for memory storage and retrieval mechanisms.
"""

from abc import ABC, abstractmethod


class BaseMemory(ABC):
    """Abstract base class for memory engines."""

    @abstractmethod
    async def add_memory(self, session_id: str, content: str, role: str) -> None:
        """Add a new memory to the store."""
        pass

    @abstractmethod
    async def get_relevant_memories(self, session_id: str, query: str, limit: int = 5) -> list[str]:
        """Retrieve memories relevant to the current query."""
        pass

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        """Clear all memories for a session."""
        pass
