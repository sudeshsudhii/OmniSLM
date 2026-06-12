"""
OmniSLM Embedder Interface.

Defines the contract for text embedding models.
"""

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """Abstract base class for embedding models.

    Embedding models convert text into dense vector representations
    for semantic search, memory, and RAG.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the embedding provider (e.g., 'sentence_transformers')."""

    @property
    @abstractmethod
    def vector_dimension(self) -> int:
        """Dimension of the generated embeddings."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Generate an embedding for a single search query."""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of documents."""
