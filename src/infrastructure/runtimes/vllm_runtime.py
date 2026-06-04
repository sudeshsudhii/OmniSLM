"""
OmniSLM — vLLM Runtime Adapter (Stub).

Integrates with the vLLM OpenAI-compatible server.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from src.core.interfaces.runtime import BaseRuntime
from src.core.registry.runtime_registry import runtime_registry
from src.core.types import CompletionChunk, ModelInfo, ModelRuntime


class VLLMRuntime(BaseRuntime):
    """Adapter for the vLLM inference engine."""

    @property
    def provider_name(self) -> str:
        return ModelRuntime.VLLM.value

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or "http://localhost:8000/v1"
        # TODO: Initialize OpenAI async client pointing to vLLM

    async def close(self) -> None:
        pass

    async def is_available(self) -> bool:
        return False  # Stub

    async def list_models(self) -> list[ModelInfo]:
        return []  # Stub

    async def get_model_info(self, model_name: str) -> dict[str, Any]:
        return {}  # Stub

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
        raise NotImplementedError("vLLM integration pending")

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
        raise NotImplementedError("vLLM integration pending")

    async def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        stop: list[str] | None = None,
    ) -> AsyncGenerator[CompletionChunk, None]:
        raise NotImplementedError("vLLM integration pending")
        yield  # type: ignore


# Register the runtime
runtime_registry.register(ModelRuntime.VLLM.value, VLLMRuntime)
