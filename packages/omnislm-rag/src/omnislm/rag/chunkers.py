"""
OmniSLM Text Chunkers.

Built-in chunking strategies for document processing.
"""

from __future__ import annotations

from typing import Any

from omnislm.core.interfaces.rag import BaseChunker
from omnislm.core.types import Chunk, Document


class CharacterChunker(BaseChunker):
    """Splits text by character count with configurable overlap."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._separator = separator

    def chunk(self, documents: list[Document]) -> list[Chunk]:
        chunks = []
        for doc in documents:
            text_chunks = self.chunk_text(doc.content, doc.metadata)
            chunks.extend(text_chunks)
        return chunks

    def chunk_text(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[Chunk]:
        meta = metadata or {}
        splits = text.split(self._separator)
        chunks: list[Chunk] = []
        current = ""

        for split in splits:
            if len(current) + len(split) + len(self._separator) > self._chunk_size:
                if current:
                    chunks.append(
                        Chunk(
                            content=current.strip(),
                            metadata={**meta, "chunk_index": len(chunks)},
                        )
                    )
                current = split
            else:
                current = (
                    f"{current}{self._separator}{split}" if current else split
                )

        if current.strip():
            chunks.append(
                Chunk(
                    content=current.strip(),
                    metadata={**meta, "chunk_index": len(chunks)},
                )
            )

        return chunks


class RecursiveChunker(BaseChunker):
    """Recursively splits text using multiple separators."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, documents: list[Document]) -> list[Chunk]:
        chunks = []
        for doc in documents:
            chunks.extend(self.chunk_text(doc.content, doc.metadata))
        return chunks

    def chunk_text(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[Chunk]:
        meta = metadata or {}
        final_chunks = self._recursive_split(text, self._separators)
        return [
            Chunk(content=c.strip(), metadata={**meta, "chunk_index": i})
            for i, c in enumerate(final_chunks)
            if c.strip()
        ]

    def _recursive_split(
        self, text: str, separators: list[str]
    ) -> list[str]:
        if not text:
            return []

        if len(text) <= self._chunk_size:
            return [text]

        separator = separators[0] if separators else ""
        remaining_seps = separators[1:] if len(separators) > 1 else []

        if separator:
            splits = text.split(separator)
        else:
            # Character-level fallback
            return [
                text[i : i + self._chunk_size]
                for i in range(0, len(text), self._chunk_size - self._chunk_overlap)
            ]

        chunks: list[str] = []
        current = ""

        for split in splits:
            candidate = f"{current}{separator}{split}" if current else split
            if len(candidate) > self._chunk_size:
                if current:
                    chunks.append(current)
                if len(split) > self._chunk_size and remaining_seps:
                    chunks.extend(self._recursive_split(split, remaining_seps))
                    current = ""
                else:
                    current = split
            else:
                current = candidate

        if current:
            chunks.append(current)

        return chunks
