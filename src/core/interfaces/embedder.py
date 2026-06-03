"""
OmniSLM Embedder Interface.

Defines the contract for text embedding models.
"""

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """Abstract base class for embedding models."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the embedding provider (e.g., 'sentence_transformers')."""
        pass

    @property
    @abstractmethod
    def vector_dimension(self) -> int:
        """Dimension of the generated embeddings."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Generate an embedding for a single search query."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of documents."""
        pass
