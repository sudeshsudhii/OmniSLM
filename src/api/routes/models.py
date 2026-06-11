"""
OmniSLM Model Routes — /api/v1/models/*
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.dependencies import Auth, get_default_runtime
from src.api.schemas import ModelListResponse, ModelResponse, PullModelRequest
from src.core.exceptions import ModelNotFoundError, RuntimeNotAvailableError
from src.core.interfaces.runtime import BaseRuntime

router = APIRouter(prefix="/models", tags=["Models"])


@router.get(
    "",
    response_model=ModelListResponse,
    summary="List available models",
)
async def list_models(
    auth: Auth,
    runtime: BaseRuntime = Depends(get_default_runtime),
) -> ModelListResponse:
    """List all locally available models from the runtime."""
    try:
        models = await runtime.list_models()
        return ModelListResponse(
            data=[
                ModelResponse(
                    id=m.id,
                    name=m.name,
                    family=m.family,
                    parameters=m.parameters,
                    quantization=m.quantization,
                    runtime=m.runtime.value,
                    context_length=m.context_length,
                    capabilities=m.capabilities,
                    status=m.status.value,
                    size_bytes=m.size_bytes,
                )
                for m in models
            ]
        )
    except RuntimeNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        ) from e


@router.get(
    "/{model_id:path}/info",
    summary="Get model details",
)
async def get_model_info(
    model_id: str,
    auth: Auth,
    runtime: BaseRuntime = Depends(get_default_runtime),
) -> dict:
    """Get detailed information about a specific model."""
    try:
        return await runtime.get_model_info(model_id)
    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        ) from e


@router.post(
    "/pull",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Pull/download a model",
)
async def pull_model(
    body: PullModelRequest,
    auth: Auth,
    runtime: BaseRuntime = Depends(get_default_runtime),
) -> StreamingResponse:
    """Pull a model from the runtime library. Streams download progress."""
    import json

    async def progress_stream():
        try:
            # We assume the runtime has a pull_model method, even though it's
            # not strictly in BaseRuntime yet (or we should add it to BaseRuntime).
            # For now, if the runtime supports it, we yield.
            if hasattr(runtime, "pull_model"):
                async for event in runtime.pull_model(body.name):  # type: ignore
                    yield f"data: {json.dumps(event)}\n\n"
                yield "data: [DONE]\n\n"
            else:
                yield f'data: {{"error": "Runtime does not support pull_model"}}\n\n'
        except ModelNotFoundError:
            yield f'data: {{"error": "Model \'{body.name}\' not found"}}\n\n'

    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
