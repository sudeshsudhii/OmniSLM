"""
OmniSLM — Ollama Runtime Adapter.

Full implementation integrating with the Ollama REST API
for model management and inference (streaming and non-streaming).
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from omnislm.core.exceptions import (
    ModelInferenceError,
    ModelNotFoundError,
    RuntimeNotAvailableError,
)
from omnislm.core.interfaces.runtime import BaseRuntime
from omnislm.core.types import CompletionChunk, FinishReason, ModelInfo, ModelRuntime, ModelStatus

logger = logging.getLogger(__name__)


class OllamaRuntime(BaseRuntime):
    """Adapter for the Ollama inference runtime.

    Communicates with the Ollama HTTP API to list/pull/load models
    and generate completions (streaming and non-streaming).

    Args:
        base_url: Ollama server URL (default: http://localhost:11434).
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    @property
    def provider_name(self) -> str:
        return ModelRuntime.OLLAMA.value

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(
                    connect=10.0, read=300.0, write=10.0, pool=10.0
                ),
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            # Lazy initialization for convenience
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(
                    connect=10.0, read=300.0, write=10.0, pool=10.0
                ),
            )
        return self._client

    # ---- Health ----

    async def is_available(self) -> bool:
        """Check if Ollama is running and reachable."""
        try:
            resp = await self._get_client().get("/")
            return resp.status_code == 200
        except Exception:
            return False

    # ---- Model Management ----

    async def list_models(self) -> list[ModelInfo]:
        """List all locally available models."""
        try:
            resp = await self._get_client().get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            logger.error("Failed to list Ollama models: %s", e)
            raise RuntimeNotAvailableError("ollama") from e

        models: list[ModelInfo] = []
        for m in data.get("models", []):
            name = m.get("name", "")
            details = m.get("details", {})
            models.append(
                ModelInfo(
                    id=name,
                    name=name.split(":")[0] if ":" in name else name,
                    family=details.get("family", "unknown"),
                    parameters=details.get("parameter_size"),
                    quantization=details.get("quantization_level"),
                    runtime=ModelRuntime.OLLAMA,
                    context_length=4096,
                    capabilities=self._parse_capabilities(details),
                    status=ModelStatus.AVAILABLE,
                    size_bytes=m.get("size"),
                )
            )
        return models

    async def pull_model(
        self, model_name: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Pull (download) a model. Yields progress events."""
        try:
            async with self._get_client().stream(
                "POST",
                "/api/pull",
                json={"name": model_name},
                timeout=httpx.Timeout(
                    connect=10.0, read=3600.0, write=10.0, pool=10.0
                ),
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield json.loads(line)
        except httpx.HTTPError as e:
            logger.error("Failed to pull model %s: %s", model_name, e)
            raise ModelNotFoundError(model_name) from e

    async def get_model_info(self, model_name: str) -> dict[str, Any]:
        """Get detailed information about a model."""
        try:
            resp = await self._get_client().post(
                "/api/show", json={"name": model_name}
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(model_name) from e
            raise

    # ---- Inference ----

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
        """Generate a non-streaming completion."""
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
            },
        }
        if system:
            payload["system"] = system
        if stop:
            payload["options"]["stop"] = stop

        try:
            resp = await self._get_client().post("/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("Inference failed for model %s: %s", model, e)
            raise ModelInferenceError(f"Ollama inference failed: {e}") from e

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
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
            },
        }
        if stop:
            payload["options"]["stop"] = stop

        try:
            resp = await self._get_client().post("/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("Chat inference failed for model %s: %s", model, e)
            raise ModelInferenceError(f"Ollama chat failed: {e}") from e

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
        """Generate a streaming chat completion."""
        import uuid as _uuid

        msg_id = f"msg_{_uuid.uuid4().hex[:12]}"

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
            },
        }
        if stop:
            payload["options"]["stop"] = stop

        try:
            async with self._get_client().stream(
                "POST", "/api/chat", json=payload
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    message = data.get("message", {})
                    content = message.get("content", "")
                    done = data.get("done", False)

                    chunk = CompletionChunk(
                        id=msg_id,
                        content=content,
                        model=model,
                        finish_reason=None,
                    )

                    if done:
                        chunk.finish_reason = FinishReason.STOP
                        chunk.prompt_tokens = data.get("prompt_eval_count")
                        chunk.completion_tokens = data.get("eval_count")
                        if chunk.prompt_tokens and chunk.completion_tokens:
                            chunk.total_tokens = (
                                chunk.prompt_tokens + chunk.completion_tokens
                            )

                    yield chunk

        except httpx.HTTPError as e:
            logger.error("Streaming chat failed for model %s: %s", model, e)
            raise ModelInferenceError(
                f"Ollama streaming failed: {e}"
            ) from e

    # ---- Helpers ----

    @staticmethod
    def _parse_capabilities(details: dict[str, Any]) -> list[str]:
        caps = ["chat"]
        family = details.get("family", "").lower()
        if family in ("qwen", "llama", "phi", "mistral", "gemma"):
            caps.append("code")
        return caps
