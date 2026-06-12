"""
OmniSLM Semantic Memory — Vector-backed semantic recall.
"""

from __future__ import annotations

from typing import Any

from omnislm.core.interfaces.embedder import BaseEmbedder
from omnislm.core.interfaces.memory import BaseSemanticMemory
from omnislm.core.interfaces.rag import BaseVectorStore


class SemanticMemory(BaseSemanticMemory):
    """Long-term semantic memory backed by a vector database.

    Stores conversational facts and retrieves them based on
    semantic similarity to the current user query.
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedder: BaseEmbedder,
        collection_name: str = "semantic_memory",
    ) -> None:
        self._vector_store = vector_store
        self._embedder = embedder
        self._collection_name = collection_name

    async def add(self, session_id: str, content: str, role: str, **metadata: Any) -> None:
        from omnislm.core.types import Chunk

        embedding = await self._embedder.embed_query(content)
        chunk = Chunk(
            content=content,
            metadata={"session_id": session_id, "role": role, **metadata},
            embedding=embedding,
        )
        await self._vector_store.add_documents(self._collection_name, [chunk])

    async def recall(
        self, session_id: str, query: str, *, limit: int = 5
    ) -> list[dict[str, Any]]:
        query_vector = await self._embedder.embed_query(query)
        results = await self._vector_store.search(
            self._collection_name,
            query_vector,
            limit=limit,
            score_threshold=0.5,
            filters={"session_id": session_id},
        )
        return [
            {"content": r.content, "score": r.score, **r.metadata}
            for r in results
        ]

    async def search(
        self,
        session_id: str,
        query_vector: list[float],
        *,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        results = await self._vector_store.search(
            self._collection_name,
            query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filters={"session_id": session_id},
        )
        return [
            {"content": r.content, "score": r.score, **r.metadata}
            for r in results
        ]

    async def clear(self, session_id: str) -> None:
        # Delete by session_id filter — implementation depends on vector store
        pass
