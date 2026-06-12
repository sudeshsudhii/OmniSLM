"""
OmniSLM — vLLM Runtime Adapter.

Integrates with vLLM's OpenAI-compatible API server.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from omnislm.core.exceptions import ModelInferenceError, RuntimeNotAvailableError
from omnislm.core.interfaces.runtime import BaseRuntime
from omnislm.core.types import CompletionChunk, FinishReason, ModelInfo, ModelRuntime

logger = logging.getLogger(__name__)


class VLLMRuntime(BaseRuntime):
    """Adapter for the vLLM inference engine (OpenAI-compatible API)."""

    def __init__(self, base_url: str = "http://localhost:8000/v1") -> None:
        self._base_url = base_url.rstrip("/")
        self._client: Any = None

    @property
    def provider_name(self) -> str:
        return ModelRuntime.VLLM.value

    async def initialize(self) -> None:
        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                base_url=self._base_url, api_key="not-needed"
            )
        except ImportError:
            logger.warning("openai package not installed for vLLM runtime")

    async def close(self) -> None:
        if self._client and hasattr(self._client, "close"):
            await self._client.close()

    async def is_available(self) -> bool:
        if not self._client:
            return False
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False

    async def list_models(self) -> list[ModelInfo]:
        if not self._client:
            return []
        try:
            response = await self._client.models.list()
            return [
                ModelInfo(
                    id=m.id,
                    name=m.id,
                    family="unknown",
                    runtime=ModelRuntime.VLLM,
                )
                for m in response.data
            ]
        except Exception:
            return []

    async def get_model_info(self, model_name: str) -> dict[str, Any]:
        return {"id": model_name, "runtime": "vllm"}

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
        if not self._client:
            raise RuntimeNotAvailableError("vllm")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
        )

        return {
            "message": {"content": response.choices[0].message.content},
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }

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
        if not self._client:
            raise RuntimeNotAvailableError("vllm")

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
        )

        return {
            "message": {"content": response.choices[0].message.content},
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }

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
        if not self._client:
            raise RuntimeNotAvailableError("vllm")

        import uuid

        msg_id = f"msg_{uuid.uuid4().hex[:12]}"

        stream = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
            stream=True,
        )

        async for chunk_data in stream:
            delta = chunk_data.choices[0].delta if chunk_data.choices else None
            content = delta.content if delta and delta.content else ""
            finish = chunk_data.choices[0].finish_reason if chunk_data.choices else None

            yield CompletionChunk(
                id=msg_id,
                content=content,
                model=model,
                finish_reason=FinishReason.STOP if finish == "stop" else None,
            )
