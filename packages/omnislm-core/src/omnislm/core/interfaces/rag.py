"""
OmniSLM RAG Pipeline Interfaces.

Contracts for the RAG (Retrieval-Augmented Generation) subsystem:
- Loaders: extract text from files and sources
- Chunkers: split documents into smaller pieces
- Retrievers: find relevant chunks for a query
- Rerankers: re-score and reorder retrieved chunks
- Vector Stores: persist and search document embeddings
"""

from abc import ABC, abstractmethod
from typing import Any

from omnislm.core.types import Chunk, Document, RetrievalResult


class BaseLoader(ABC):
    """Abstract base class for document loaders.

    Loaders extract text content from various sources
    (files, URLs, databases, APIs) into Document objects.
    """

    @abstractmethod
    async def load(self) -> list[Document]:
        """Load and return documents from the source."""

    @abstractmethod
    def supports(self, source: str) -> bool:
        """Check if this loader supports the given source type/path."""


class BaseChunker(ABC):
    """Abstract base class for text chunkers (splitters).

    Chunkers break documents into smaller, embeddable chunks
    while preserving semantic coherence.
    """

    @abstractmethod
    def chunk(self, documents: list[Document]) -> list[Chunk]:
        """Split documents into chunks."""

    @abstractmethod
    def chunk_text(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split a single text string into chunks."""


class BaseRetriever(ABC):
    """Abstract base class for document retrievers.

    Retrievers take a query and return the most relevant chunks
    from the document store.
    """

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Retrieve relevant documents for the query.

        Args:
            query: The search query text.
            limit: Maximum number of results.
            filters: Optional metadata filters.

        Returns:
            List of RetrievalResult objects sorted by relevance.
        """


class BaseReranker(ABC):
    """Abstract base class for result rerankers.

    Rerankers take an initial set of results and re-score them
    using a more expensive but accurate model (e.g., cross-encoder).
    """

    @abstractmethod
    async def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        *,
        limit: int | None = None,
    ) -> list[RetrievalResult]:
        """Re-rank results based on the query.

        Args:
            query: The original search query.
            results: Initial retrieval results to re-rank.
            limit: Optional limit on returned results.

        Returns:
            Re-ranked list of RetrievalResult objects.
        """


class BaseVectorStore(ABC):
    """Abstract base class for vector stores.

    Vector stores persist document embeddings and support
    similarity search operations.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store (create collections, etc.)."""

    @abstractmethod
    async def add_documents(
        self,
        collection: str,
        chunks: list[Chunk],
    ) -> list[str]:
        """Add document chunks with embeddings to the store.

        Returns:
            List of assigned document IDs.
        """

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: list[float],
        *,
        limit: int = 5,
        score_threshold: float = 0.5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Search for similar vectors."""

    @abstractmethod
    async def delete(
        self,
        collection: str,
        document_ids: list[str],
    ) -> None:
        """Delete documents by ID."""

    @abstractmethod
    async def close(self) -> None:
        """Close connections to the vector store."""
