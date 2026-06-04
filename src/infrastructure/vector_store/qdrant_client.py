"""
OmniSLM Vector Store Adapter.

Integrates with Qdrant for storing and retrieving document chunks and memory nodes.
"""

from typing import Any
import uuid

from src.config.settings import get_settings

try:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
except ImportError:
    AsyncQdrantClient = None
    Distance = None
    VectorParams = None
    PointStruct = None

settings = get_settings()


class QdrantAdapter:
    """Async client for Qdrant vector database."""

    def __init__(self, url: str | None = None):
        if AsyncQdrantClient is None:
            raise ImportError(
                "qdrant-client is not installed. "
                "Install it with `pip install qdrant-client`."
            )
        self.url = url or getattr(settings, "qdrant_url", "http://localhost:6333")
        self.client = AsyncQdrantClient(url=self.url)

    async def ensure_collection(self, collection_name: str, vector_size: int = 384) -> None:
        """Create a collection if it doesn't exist."""
        exists = await self.client.collection_exists(collection_name)
        if not exists:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    async def upsert_documents(
        self,
        collection_name: str,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
        ids: list[str] | None = None,
    ) -> None:
        """Upsert vectors and their payloads into a collection."""
        if not ids:
            ids = [uuid.uuid4().hex for _ in vectors]
            
        points = [
            PointStruct(id=point_id, vector=vector, payload=payload)
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]
        
        await self.client.upsert(
            collection_name=collection_name,
            points=points,
        )

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Search for the most similar vectors."""
        results = await self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    async def close(self) -> None:
        """Close the async client."""
        await self.client.close()
