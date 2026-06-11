"""
OmniSLM Chat Routes — /api/v1/chat/* and /api/v1/conversations/*
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.dependencies import Auth, get_chat_service
from src.api.schemas import (
    ChatCompletionRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
)
from src.core.exceptions import ModelInferenceError, NotFoundError
from src.core.types import ChatMessage, MessageRole
from src.services.chat_service import ChatService

chat_router = APIRouter(prefix="/chat", tags=["Chat"])
conversation_router = APIRouter(prefix="/conversations", tags=["Conversations"])


# ============================================================
#  Chat Completions
# ============================================================


@chat_router.post(
    "/completions",
    summary="Create chat completion (streaming)",
    response_class=StreamingResponse,
)
async def create_chat_completion(
    body: ChatCompletionRequest,
    auth: Auth,
    chat_service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """Create a streaming chat completion using Server-Sent Events (SSE).

    Compatible with the OpenAI API format for easy migration.
    """
    # Convert schema messages to domain objects
    messages = [
        ChatMessage(
            role=MessageRole(msg.role),
            content=msg.content,
            name=msg.name,
        )
        for msg in body.messages
    ]

    conv_id = uuid.UUID(body.conversation_id) if body.conversation_id else None

    async def event_stream():
        try:
            async for chunk in chat_service.create_completion_stream(
                auth=auth,
                model=body.model,
                messages=messages,
                conversation_id=conv_id,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                top_p=body.top_p,
                system_prompt=body.system_prompt,
            ):
                # Format as OpenAI-compatible SSE
                event_data = {
                    "id": chunk.id,
                    "object": "chat.chunk",
                    "model": chunk.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": chunk.content},
                            "finish_reason": chunk.finish_reason.value
                            if chunk.finish_reason
                            else None,
                        }
                    ],
                }

                # Add usage on final chunk
                if chunk.finish_reason:
                    event_data["usage"] = {
                        "prompt_tokens": chunk.prompt_tokens,
                        "completion_tokens": chunk.completion_tokens,
                        "total_tokens": chunk.total_tokens,
                    }

                yield f"data: {json.dumps(event_data)}\n\n"

            yield "data: [DONE]\n\n"

        except ModelInferenceError as e:
            error = {"error": {"message": e.message, "code": e.code}}
            yield f"data: {json.dumps(error)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
#  Conversations
# ============================================================


@conversation_router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a conversation",
)
async def create_conversation(
    body: CreateConversationRequest,
    auth: Auth,
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationResponse:
    """Create a new conversation."""
    result = await chat_service.create_conversation(
        auth=auth,
        title=body.title,
        model_id=body.model_id,
        system_prompt=body.system_prompt,
    )
    return ConversationResponse(**result)


@conversation_router.get(
    "",
    response_model=ConversationListResponse,
    summary="List conversations",
)
async def list_conversations(
    auth: Auth,
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationListResponse:
    """List all conversations for the current user."""
    conversations = await chat_service.list_conversations(auth)
    return ConversationListResponse(
        data=[ConversationResponse(**c) for c in conversations]
    )


@conversation_router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation with messages",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    auth: Auth,
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationDetailResponse:
    """Get a conversation with all its messages."""
    try:
        result = await chat_service.get_conversation(auth, conversation_id)
        return ConversationDetailResponse(**result)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        ) from e


@conversation_router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    auth: Auth,
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    """Soft-delete a conversation."""
    try:
        await chat_service.delete_conversation(auth, conversation_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        ) from e
