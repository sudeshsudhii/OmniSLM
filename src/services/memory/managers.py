"""
OmniSLM Memory Managers.

Implementations of different memory tiers (Session, Semantic).
"""

from typing import Any

from src.core.interfaces.embedder import BaseEmbedder
from src.core.interfaces.memory import BaseMemory
from src.infrastructure.vector_store.qdrant_client import QdrantAdapter


class SemanticMemory(BaseMemory):
    """Long-term semantic memory backed by a vector database.
    
    Stores conversational facts and retrieves them based on semantic similarity
    to the current user query.
    """

    def __init__(self, vector_store: QdrantAdapter, embedder: BaseEmbedder):
        self.vector_store = vector_store
        self.embedder = embedder
        self.collection_name = "semantic_memory"

    async def initialize(self) -> None:
        """Ensure the underlying vector collection exists."""
        await self.vector_store.ensure_collection(
            self.collection_name, 
            vector_size=self.embedder.vector_dimension
        )

    async def add_memory(self, session_id: str, content: str, role: str) -> None:
        """Embed a new memory node and store it in Qdrant."""
        vector = await self.embedder.embed_query(content)
        payload = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "type": "conversation_node"
        }
        
        await self.vector_store.upsert_documents(
            collection_name=self.collection_name,
            vectors=[vector],
            payloads=[payload]
        )

    async def get_relevant_memories(self, session_id: str, query: str, limit: int = 5) -> list[str]:
        """Search for relevant memories based on the query."""
        query_vector = await self.embedder.embed_query(query)
        
        # In a real implementation, we would apply a filter for the specific session_id
        # using Qdrant's filter parameters. For now, we just search the collection.
        results = await self.vector_store.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=0.6,
        )
        
        # Filter manually for this basic stub, though DB filtering is preferred.
        memories = [
            hit["payload"]["content"]
            for hit in results
            if hit["payload"].get("session_id") == session_id
        ]
        
        return memories

    async def clear(self, session_id: str) -> None:
        """Not implemented for semantic memory in this stub."""
        pass


class SessionMemory(BaseMemory):
    """Short-term session memory (typically backed by Redis)."""
    
    def __init__(self, redis_client: Any):
        self.redis = redis_client

    async def add_memory(self, session_id: str, content: str, role: str) -> None:
        # Append to a Redis list
        pass

    async def get_relevant_memories(self, session_id: str, query: str, limit: int = 5) -> list[str]:
        # Return the last N messages
        return []

    async def clear(self, session_id: str) -> None:
        pass
