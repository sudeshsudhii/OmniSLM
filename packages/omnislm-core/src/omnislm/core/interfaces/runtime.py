"""
OmniSLM Runtime Interface.

Defines the contract for all LLM inference runtimes (Ollama, vLLM, llama.cpp, etc.).
This interface must remain stable — runtimes are swapped via configuration only.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from omnislm.core.types import ChatMessage, CompletionChunk, ModelInfo


class BaseRuntime(ABC):
    """Abstract base class for LLM inference runtimes.

    All runtime adapters (Ollama, vLLM, llama.cpp, Transformers, ONNX)
    must implement this interface.

    Example:
        class MyCustomRuntime(BaseRuntime):
            @property
            def provider_name(self) -> str:
                return "my_runtime"
            ...
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the runtime provider (e.g., 'ollama', 'vllm')."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the runtime (establish connections, warm up, etc.)."""

    @abstractmethod
    async def close(self) -> None:
        """Cleanup runtime resources (e.g., close HTTP clients)."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the runtime is reachable/healthy."""

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models in this runtime."""

    @abstractmethod
    async def get_model_info(self, model_name: str) -> dict[str, Any]:
        """Get detailed information about a specific model."""

    @abstractmethod
    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        stop: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate a non-streaming text completion."""

    @abstractmethod
    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        stop: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate a non-streaming chat completion."""

    @abstractmethod
    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        stop: list[str] | None = None,
    ) -> AsyncGenerator[CompletionChunk, None]:
        """Generate a streaming chat completion yielding CompletionChunks."""
