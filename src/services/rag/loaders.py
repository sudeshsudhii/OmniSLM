"""
OmniSLM Document Loaders.

Extracts text from various file formats and sources.
"""

from abc import ABC, abstractmethod
from typing import Any


class Document(ABC):
    """A loaded document with text and metadata."""
    
    def __init__(self, content: str, metadata: dict[str, Any] | None = None):
        self.content = content
        self.metadata = metadata or {}


class BaseLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    def load(self) -> list[Document]:
        """Load and return documents."""
        pass


class TextLoader(BaseLoader):
    """Loads a plain text file."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> list[Document]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        return [Document(content=text, metadata={"source": self.file_path})]


class PDFLoader(BaseLoader):
    """Stub loader for PDF files. Requires pypdf or pdfplumber."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> list[Document]:
        # In a real implementation, we'd use pypdf here.
        return [Document(content=f"[Extracted PDF content from {self.file_path}]", metadata={"source": self.file_path, "type": "pdf"})]


class WebLoader(BaseLoader):
    """Stub loader for web pages. Requires BeautifulSoup4."""

    def __init__(self, url: str):
        self.url = url

    def load(self) -> list[Document]:
        # In a real implementation, fetch URL and parse HTML
        return [Document(content=f"[Extracted HTML content from {self.url}]", metadata={"source": self.url, "type": "web"})]
