"""
OmniSLM Memory Manager — Orchestrates multi-tier memory.
"""

from __future__ import annotations

import logging
from typing import Any

from omnislm.core.interfaces.memory import BaseMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """Orchestrates multiple memory tiers.

    Provides a unified interface for adding and recalling memories
    across session, conversation, semantic, and long-term tiers.
    """

    def __init__(self) -> None:
        self._tiers: dict[str, BaseMemory] = {}

    def register_tier(self, tier_name: str, memory: BaseMemory) -> None:
        """Register a memory tier."""
        self._tiers[tier_name] = memory

    async def add(
        self,
        session_id: str,
        content: str,
        role: str,
        tiers: list[str] | None = None,
        **metadata: Any,
    ) -> None:
        """Add a memory to specified tiers (or all)."""
        target_tiers = tiers or list(self._tiers.keys())
        for tier_name in target_tiers:
            if tier_name in self._tiers:
                try:
                    await self._tiers[tier_name].add(
                        session_id, content, role, **metadata
                    )
                except Exception as e:
                    logger.error(
                        "Failed to add memory to tier '%s': %s", tier_name, e
                    )

    async def recall(
        self, session_id: str, query: str, *, limit: int = 5
    ) -> dict[str, list[dict[str, Any]]]:
        """Recall memories from all tiers."""
        results: dict[str, list[dict[str, Any]]] = {}
        for tier_name, memory in self._tiers.items():
            try:
                results[tier_name] = await memory.recall(
                    session_id, query, limit=limit
                )
            except Exception as e:
                logger.error("Failed to recall from tier '%s': %s", tier_name, e)
                results[tier_name] = []
        return results

    def get_tier(self, tier_name: str) -> BaseMemory | None:
        return self._tiers.get(tier_name)

    def list_tiers(self) -> list[str]:
        return list(self._tiers.keys())
