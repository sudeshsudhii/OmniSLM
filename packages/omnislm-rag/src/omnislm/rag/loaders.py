"""
OmniSLM Document Loaders.

Built-in loaders for text, PDF, and web sources.
"""

from __future__ import annotations

from typing import Any

from omnislm.core.interfaces.rag import BaseLoader
from omnislm.core.types import Document


class TextLoader(BaseLoader):
    """Loads plain text files."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    async def load(self) -> list[Document]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return [Document(content=text, metadata={"source": self.file_path, "type": "text"})]

    def supports(self, source: str) -> bool:
        return source.endswith((".txt", ".md", ".rst"))


class PDFLoader(BaseLoader):
    """Loads PDF files using pypdf."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    async def load(self) -> list[Document]:
        try:
            from pypdf import PdfReader

            reader = PdfReader(self.file_path)
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(
                        Document(
                            content=text,
                            metadata={
                                "source": self.file_path,
                                "type": "pdf",
                                "page": i,
                            },
                        )
                    )
            return pages
        except ImportError:
            return [
                Document(
                    content=f"[PDF loading requires pypdf: {self.file_path}]",
                    metadata={"source": self.file_path, "type": "pdf"},
                )
            ]

    def supports(self, source: str) -> bool:
        return source.endswith(".pdf")


class MarkdownLoader(BaseLoader):
    """Loads Markdown files."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    async def load(self) -> list[Document]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return [
            Document(
                content=text,
                metadata={"source": self.file_path, "type": "markdown"},
            )
        ]

    def supports(self, source: str) -> bool:
        return source.endswith((".md", ".markdown"))
