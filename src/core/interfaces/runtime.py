"""
OmniSLM Runtime Interface.

Defines the contract for all LLM inference runtimes (Ollama, vLLM, etc.).
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from src.core.types import ChatMessage, CompletionChunk, ModelInfo


class BaseRuntime(ABC):
    """Abstract base class for LLM inference runtimes."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the runtime provider (e.g., 'ollama', 'vllm')."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Cleanup runtime resources (e.g., close HTTP clients)."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the runtime is reachable/healthy."""
        pass

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models in this runtime."""
        pass

    @abstractmethod
    async def get_model_info(self, model_name: str) -> dict[str, Any]:
        """Get detailed information about a specific model."""
        pass

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
        pass

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
        pass

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
        pass
