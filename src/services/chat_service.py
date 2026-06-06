"""
OmniSLM Chat Service.

Orchestrates the chat completion lifecycle:
prompt building → model inference → message storage.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.core.exceptions import ModelInferenceError, NotFoundError
from src.core.types import AuthContext, ChatMessage, CompletionChunk, FinishReason, MessageRole
from src.core.interfaces.runtime import BaseRuntime
from src.infrastructure.database.models import Conversation, Message

logger = get_logger(__name__)


class ChatService:
    """Application service for chat completions and conversation management."""

    def __init__(self, db: AsyncSession, runtime: BaseRuntime):
        self.db = db
        self.runtime = runtime

    # ---- Conversations ----

    async def create_conversation(
        self,
        auth: AuthContext,
        title: str | None = None,
        model_id: str | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        """Create a new conversation."""
        conversation = Conversation(
            tenant_id=auth.tenant_id,
            user_id=auth.user_id,
            title=title or "New Conversation",
            model_id=model_id,
            system_prompt=system_prompt,
        )
        self.db.add(conversation)
        await self.db.flush()

        logger.info("Conversation created", conversation_id=str(conversation.id))
        return self._serialize_conversation(conversation)

    async def list_conversations(self, auth: AuthContext) -> list[dict]:
        """List all conversations for the current user."""
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.tenant_id == auth.tenant_id,
                Conversation.user_id == auth.user_id,
                Conversation.status == "active",
            )
            .order_by(Conversation.updated_at.desc())
        )
        conversations = result.scalars().all()
        return [self._serialize_conversation(c) for c in conversations]

    async def get_conversation(self, auth: AuthContext, conversation_id: uuid.UUID) -> dict:
        """Get a single conversation with messages."""
        conv = await self._get_conversation(auth, conversation_id)
        data = self._serialize_conversation(conv)
        data["messages"] = [self._serialize_message(m) for m in conv.messages]
        return data

    async def delete_conversation(self, auth: AuthContext, conversation_id: uuid.UUID) -> None:
        """Soft-delete a conversation."""
        conv = await self._get_conversation(auth, conversation_id)
        conv.status = "deleted"
        await self.db.flush()
        logger.info("Conversation deleted", conversation_id=str(conversation_id))

    # ---- Chat Completions ----

    async def create_completion_stream(
        self,
        auth: AuthContext,
        model: str,
        messages: list[ChatMessage],
        conversation_id: uuid.UUID | None = None,
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[CompletionChunk, None]:
        """Create a streaming chat completion.

        1. Resolves or creates conversation.
        2. Saves user message.
        3. Builds prompt and calls model.
        4. Streams tokens and saves assistant response.
        """
        start_time = time.monotonic()

        # Resolve conversation
        conversation = None
        if conversation_id:
            try:
                conversation = await self._get_conversation(auth, conversation_id)
            except NotFoundError:
                pass

        if not conversation:
            conv = Conversation(
                tenant_id=auth.tenant_id,
                user_id=auth.user_id,
                title=messages[-1].content[:100] if messages else "New Chat",
                model_id=model,
                system_prompt=system_prompt,
            )
            self.db.add(conv)
            await self.db.flush()
            conversation = conv
            conversation_id = conv.id

        # Save user message
        user_msg = messages[-1] if messages else None
        if user_msg and user_msg.role == MessageRole.USER:
            db_msg = Message(
                conversation_id=conversation.id,
                role="user",
                content=user_msg.content,
            )
            self.db.add(db_msg)
            conversation.message_count += 1
            await self.db.flush()

        # Build messages for Ollama
        ollama_messages = []
        if system_prompt or conversation.system_prompt:
            ollama_messages.append({
                "role": "system",
                "content": system_prompt or conversation.system_prompt or "",
            })
        for msg in messages:
            ollama_messages.append({"role": msg.role.value, "content": msg.content})

        # Stream from model
        full_response = []
        final_chunk: CompletionChunk | None = None

        try:
            async for chunk in self.runtime.chat_stream(
                model=model,
                messages=ollama_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            ):
                full_response.append(chunk.content)
                final_chunk = chunk
                yield chunk

        except ModelInferenceError:
            raise
        except Exception as e:
            logger.error("Chat stream error", error=str(e), model=model)
            raise ModelInferenceError(f"Stream failed: {e}") from e

        # Save assistant message
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        assistant_content = "".join(full_response)

        if assistant_content:
            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=assistant_content,
                model_id=model,
                latency_ms=elapsed_ms,
                token_count=final_chunk.total_tokens if final_chunk else None,
                finish_reason=final_chunk.finish_reason.value if final_chunk and final_chunk.finish_reason else "stop",
            )
            self.db.add(assistant_msg)
            conversation.message_count += 1
            conversation.last_message_at = assistant_msg.created_at
            await self.db.flush()

        logger.info(
            "Chat completion finished",
            model=model,
            conversation_id=str(conversation_id),
            latency_ms=elapsed_ms,
            tokens=final_chunk.total_tokens if final_chunk else None,
        )

    # ---- Private Helpers ----

    async def _get_conversation(self, auth: AuthContext, conv_id: uuid.UUID) -> Conversation:
        """Fetch a conversation ensuring tenant/user ownership."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conv_id,
                Conversation.tenant_id == auth.tenant_id,
                Conversation.user_id == auth.user_id,
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise NotFoundError("Conversation", str(conv_id))
        return conv

    @staticmethod
    def _serialize_conversation(conv: Conversation) -> dict:
        return {
            "id": str(conv.id),
            "title": conv.title,
            "model_id": conv.model_id,
            "system_prompt": conv.system_prompt,
            "status": conv.status,
            "message_count": conv.message_count,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        }

    @staticmethod
    def _serialize_message(msg: Message) -> dict:
        return {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "model_id": msg.model_id,
            "token_count": msg.token_count,
            "latency_ms": msg.latency_ms,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
