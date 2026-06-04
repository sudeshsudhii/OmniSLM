"""
OmniSLM — Sentence Transformers Embedder.

Uses local sentence-transformers models (e.g., all-MiniLM-L6-v2, bge-small-en-v1.5).
"""

import asyncio
from typing import Any

from src.core.interfaces.embedder import BaseEmbedder

# Optional dependency check
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class SentenceTransformerEmbedder(BaseEmbedder):
    """Local embedding generator using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with `pip install sentence-transformers`."
            )

        self._model_name = model_name
        self._device = device
        self._model = SentenceTransformer(model_name, device=device)
        self._dimension = self._model.get_sentence_embedding_dimension()

    @property
    def provider_name(self) -> str:
        return "sentence_transformers"

    @property
    def vector_dimension(self) -> int:
        return self._dimension or 384

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        # Run synchronous embedding in a thread pool to avoid blocking async event loop
        loop = asyncio.get_running_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._model.encode(text, normalize_embeddings=True)
        )
        return embedding.tolist()

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents."""
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(texts, normalize_embeddings=True)
        )
        return embeddings.tolist()
