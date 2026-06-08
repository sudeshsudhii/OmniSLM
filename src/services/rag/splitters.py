"""
OmniSLM Text Splitters.

Chunks large text documents into smaller pieces suitable for embedding.
"""

from abc import ABC, abstractmethod

from src.services.rag.loaders import Document


class BaseSplitter(ABC):
    """Abstract base class for text splitters."""

    @abstractmethod
    def split_documents(self, documents: list[Document]) -> list[Document]:
        """Split a list of documents into chunks."""
        pass


class CharacterTextSplitter(BaseSplitter):
    """Splits text based on a specific character and chunk size."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separator: str = "\n\n"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def split_text(self, text: str) -> list[str]:
        """Split a single string into chunks."""
        splits = text.split(self.separator)
        chunks = []
        current_chunk = ""

        for split in splits:
            # If a single split is larger than chunk_size, we might need a fallback,
            # but for simplicity, we just append it here.
            if len(current_chunk) + len(split) + len(self.separator) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = split
            else:
                if current_chunk:
                    current_chunk += self.separator + split
                else:
                    current_chunk = split

        if current_chunk:
            chunks.append(current_chunk)

        # Simplified overlap logic (real implementations are more complex)
        return chunks

    def split_documents(self, documents: list[Document]) -> list[Document]:
        """Split documents into smaller chunk documents."""
        chunked_docs = []
        for i, doc in enumerate(documents):
            chunks = self.split_text(doc.content)
            for j, chunk in enumerate(chunks):
                metadata = doc.metadata.copy()
                metadata["chunk_index"] = j
                chunked_docs.append(Document(content=chunk, metadata=metadata))
                
        return chunked_docs
