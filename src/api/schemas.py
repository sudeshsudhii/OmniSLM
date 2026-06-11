"""
OmniSLM API Schemas — Pydantic request/response models.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ============================================================
#  Common
# ============================================================


class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int = 20
    total_count: int = 0
    total_pages: int = 0


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    code: str


class ErrorResponse(BaseModel):
    type: str = "https://docs.omnislm.dev/errors/error"
    title: str
    status: int
    detail: str
    instance: str | None = None
    errors: list[ErrorDetail] = []
    request_id: str | None = None


# ============================================================
#  Auth
# ============================================================


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=255)
    tenant_name: str | None = Field(None, max_length=255)


class RegisterResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    id: str
    email: str
    display_name: str | None
    tenant_id: str
    roles: list[str]
    created_at: datetime | None = None


# ============================================================
#  Models
# ============================================================


class ModelResponse(BaseModel):
    id: str
    name: str
    family: str
    parameters: str | None = None
    quantization: str | None = None
    runtime: str
    context_length: int
    capabilities: list[str] = []
    status: str
    size_bytes: int | None = None


class ModelListResponse(BaseModel):
    data: list[ModelResponse]


class PullModelRequest(BaseModel):
    name: str = Field(..., description="Model name to pull, e.g., 'qwen2.5:7b'")


# ============================================================
#  Chat
# ============================================================


class ChatMessageSchema(BaseModel):
    role: str = Field(..., description="Message role: system, user, assistant, tool")
    content: str = Field(..., description="Message content")
    name: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model ID, e.g., 'qwen2.5:7b'")
    messages: list[ChatMessageSchema] = Field(..., min_length=1)
    conversation_id: str | None = None
    stream: bool = True
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=1, le=32768)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    system_prompt: str | None = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.chunk"
    model: str
    choices: list[dict]
    usage: dict | None = None


# ============================================================
#  Conversations
# ============================================================


class CreateConversationRequest(BaseModel):
    title: str | None = Field(None, max_length=500)
    model_id: str | None = None
    system_prompt: str | None = None


class ConversationResponse(BaseModel):
    id: str
    title: str | None
    model_id: str | None
    system_prompt: str | None
    status: str
    message_count: int
    created_at: str | None
    updated_at: str | None


class ConversationListResponse(BaseModel):
    data: list[ConversationResponse]


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str | None
    model_id: str | None
    token_count: int | None
    latency_ms: int | None
    created_at: str | None


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []


# ============================================================
#  API Keys
# ============================================================


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., max_length=255)
    scopes: list[str] = []
    expires_in_days: int | None = None


class ApiKeyResponse(BaseModel):
    id: str
    key: str | None = None  # Only returned on creation
    key_prefix: str
    name: str
    scopes: list[str]
    expires_at: str | None
