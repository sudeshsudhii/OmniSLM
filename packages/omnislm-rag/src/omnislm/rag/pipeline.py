"""
OmniSLM RAG Pipeline — Orchestrates the full RAG workflow.

Load → Chunk → Embed → Store (ingestion)
Query → Embed → Retrieve → Rerank → Generate (query)
"""

from __future__ import annotations

import logging
from typing import Any

from omnislm.core.interfaces.embedder import BaseEmbedder
from omnislm.core.interfaces.rag import (
    BaseChunker,
    BaseLoader,
    BaseReranker,
    BaseRetriever,
    BaseVectorStore,
)
from omnislm.core.interfaces.runtime import BaseRuntime
from omnislm.core.types import Chunk, Document, RetrievalResult

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Orchestrates the full RAG (Retrieval-Augmented Generation) pipeline.

    Example:
        pipeline = RAGPipeline(
            embedder=my_embedder,
            vector_store=my_store,
            chunker=my_chunker,
            runtime=my_runtime,
        )

        # Ingest documents
        await pipeline.ingest([TextLoader("data.txt")])

        # Query
        answer = await pipeline.query("What is the main topic?", model="qwen2.5:7b")
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: BaseVectorStore,
        chunker: BaseChunker,
        runtime: BaseRuntime | None = None,
        retriever: BaseRetriever | None = None,
        reranker: BaseReranker | None = None,
        collection_name: str = "documents",
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._chunker = chunker
        self._runtime = runtime
        self._retriever = retriever
        self._reranker = reranker
        self._collection_name = collection_name

    async def ingest(
        self,
        loaders: list[BaseLoader],
        collection: str | None = None,
    ) -> int:
        """Ingest documents through the full pipeline.

        Load → Chunk → Embed → Store

        Returns:
            Number of chunks stored.
        """
        collection = collection or self._collection_name
        all_documents: list[Document] = []

        # 1. Load
        for loader in loaders:
            docs = await loader.load()
            all_documents.extend(docs)

        logger.info("Loaded %d documents", len(all_documents))

        # 2. Chunk
        chunks = self._chunker.chunk(all_documents)
        logger.info("Created %d chunks", len(chunks))

        # 3. Embed
        texts = [c.content for c in chunks]
        embeddings = await self._embedder.embed_documents(texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        # 4. Store
        await self._vector_store.add_documents(collection, chunks)
        logger.info("Stored %d chunks in collection '%s'", len(chunks), collection)

        return len(chunks)

    async def query(
        self,
        question: str,
        *,
        model: str = "",
        limit: int = 5,
        collection: str | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Query the RAG pipeline.

        Query → Embed → Retrieve → (Rerank) → Generate

        Returns:
            The generated answer string.
        """
        collection = collection or self._collection_name

        # 1. Embed query
        query_vector = await self._embedder.embed_query(question)

        # 2. Retrieve
        results = await self._vector_store.search(
            collection, query_vector, limit=limit
        )

        # 3. Rerank (optional)
        if self._reranker and results:
            results = await self._reranker.rerank(question, results, limit=limit)

        # 4. Build context
        context = "\n\n".join(r.content for r in results)

        # 5. Generate (if runtime available)
        if self._runtime and model:
            prompt = system_prompt or (
                "Answer the question based on the following context. "
                "If the answer is not in the context, say so.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {question}\n\n"
                "Answer:"
            )

            response = await self._runtime.generate(
                model=model,
                prompt=prompt,
                temperature=0.3,
            )

            return response.get("response", "No response generated.")

        # If no runtime, return raw context
        return f"Retrieved context:\n{context}"

    async def retrieve(
        self,
        question: str,
        *,
        limit: int = 5,
        collection: str | None = None,
    ) -> list[RetrievalResult]:
        """Retrieve relevant chunks without generation."""
        collection = collection or self._collection_name
        query_vector = await self._embedder.embed_query(question)

        results = await self._vector_store.search(
            collection, query_vector, limit=limit
        )

        if self._reranker:
            results = await self._reranker.rerank(question, results, limit=limit)

        return results
