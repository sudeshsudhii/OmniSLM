"""
OmniSLM — Ollama Runtime Adapter.

Integrates with the Ollama REST API for model management and inference.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from src.config.logging import get_logger
from src.config.settings import get_settings
from src.core.exceptions import ModelInferenceError, ModelNotFoundError, RuntimeNotAvailableError
from src.core.interfaces.runtime import BaseRuntime
from src.core.registry.runtime_registry import runtime_registry
from src.core.types import CompletionChunk, ModelInfo, ModelRuntime, ModelStatus

logger = get_logger(__name__)
settings = get_settings()


class OllamaRuntime(BaseRuntime):
    """Adapter for the Ollama inference runtime.

    Communicates with the Ollama HTTP API to list/pull/load models
    and generate completions (streaming and non-streaming).
    """

    @property
    def provider_name(self) -> str:
        return ModelRuntime.OLLAMA.value

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0),
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    # ---- Health ----

    async def is_available(self) -> bool:
        """Check if Ollama is running and reachable."""
        try:
            resp = await self._client.get("/")
            return resp.status_code == 200
        except Exception:
            return False

    # ---- Model Management ----

    async def list_models(self) -> list[ModelInfo]:
        """List all locally available models."""
        try:
            resp = await self._client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            logger.error("Failed to list Ollama models", error=str(e))
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
                    parameters=details.get("parameter_size", None),
                    quantization=details.get("quantization_level", None),
                    runtime=ModelRuntime.OLLAMA,
                    context_length=self._parse_context_length(details),
                    capabilities=self._parse_capabilities(details),
                    status=ModelStatus.AVAILABLE,
                    size_bytes=m.get("size"),
                )
            )
        return models

    async def pull_model(self, model_name: str) -> AsyncGenerator[dict[str, Any], None]:
        """Pull (download) a model from the Ollama library. Yields progress events."""
        try:
            async with self._client.stream(
                "POST",
                "/api/pull",
                json={"name": model_name},
                timeout=httpx.Timeout(connect=10.0, read=3600.0, write=10.0, pool=10.0),
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield json.loads(line)
        except httpx.HTTPError as e:
            logger.error("Failed to pull model", model=model_name, error=str(e))
            raise ModelNotFoundError(model_name) from e

    async def get_model_info(self, model_name: str) -> dict[str, Any]:
        """Get detailed information about a model."""
        try:
            resp = await self._client.post("/api/show", json={"name": model_name})
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
            resp = await self._client.post("/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("Inference failed", model=model, error=str(e))
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
            resp = await self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("Chat inference failed", model=model, error=str(e))
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
        """Generate a streaming chat completion. Yields CompletionChunks."""
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
            async with self._client.stream(
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
                        chunk.finish_reason = "stop"
                        chunk.prompt_tokens = data.get("prompt_eval_count")
                        chunk.completion_tokens = data.get("eval_count")
                        if chunk.prompt_tokens and chunk.completion_tokens:
                            chunk.total_tokens = chunk.prompt_tokens + chunk.completion_tokens

                    yield chunk

        except httpx.HTTPError as e:
            logger.error("Streaming chat failed", model=model, error=str(e))
            raise ModelInferenceError(f"Ollama streaming failed: {e}") from e

    # ---- Private Helpers ----

    @staticmethod
    def _parse_context_length(details: dict[str, Any]) -> int:
        """Parse context length from model details, defaulting to 4096."""
        # Ollama doesn't always expose this directly
        return 4096

    @staticmethod
    def _parse_capabilities(details: dict[str, Any]) -> list[str]:
        """Infer model capabilities from details."""
        caps = ["chat"]
        family = details.get("family", "").lower()
        if family in ("qwen", "llama", "phi", "mistral"):
            caps.append("code")
        return caps


# Register the runtime
runtime_registry.register(ModelRuntime.OLLAMA.value, OllamaRuntime)
