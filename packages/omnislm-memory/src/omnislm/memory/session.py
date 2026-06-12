"""
OmniSLM Session Memory — In-memory and Redis-backed session memory.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from omnislm.core.interfaces.memory import BaseSessionMemory


class InMemorySessionMemory(BaseSessionMemory):
    """In-memory session memory for development and testing.

    Stores messages in a Python dict — not persistent across restarts.
    For production, use RedisSessionMemory.
    """

    def __init__(self, max_messages: int = 100) -> None:
        self._max_messages = max_messages
        self._store: dict[str, list[dict[str, Any]]] = defaultdict(list)

    async def add(self, session_id: str, content: str, role: str, **metadata: Any) -> None:
        entry = {"content": content, "role": role, **metadata}
        self._store[session_id].append(entry)
        # Trim to max
        if len(self._store[session_id]) > self._max_messages:
            self._store[session_id] = self._store[session_id][-self._max_messages :]

    async def recall(
        self, session_id: str, query: str, *, limit: int = 5
    ) -> list[dict[str, Any]]:
        """For session memory, recall returns the most recent messages."""
        return self._store.get(session_id, [])[-limit:]

    async def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    async def get_recent(
        self, session_id: str, *, limit: int = 20
    ) -> list[dict[str, Any]]:
        return self._store.get(session_id, [])[-limit:]

    async def set_ttl(self, session_id: str, ttl_seconds: int) -> None:
        # No-op for in-memory implementation
        pass
