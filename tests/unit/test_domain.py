"""
Unit tests for domain types and exceptions.
"""

import uuid

import pytest

from src.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ModelNotFoundError,
    NotFoundError,
    OmniSLMError,
    RateLimitExceededError,
    ValidationError,
)
from src.core.types import (
    AuthContext,
    ChatMessage,
    CompletionChunk,
    MessageRole,
    ModelInfo,
    ModelRuntime,
    ModelStatus,
    TokenPair,
)


class TestExceptions:
    def test_base_error(self):
        err = OmniSLMError("test error", "TEST_CODE")
        assert err.message == "test error"
        assert err.code == "TEST_CODE"
        assert str(err) == "test error"

    def test_authentication_error(self):
        err = AuthenticationError()
        assert err.code == "AUTHENTICATION_ERROR"
        assert "Authentication failed" in err.message

    def test_not_found_error_with_id(self):
        err = NotFoundError("User", "abc-123")
        assert "User" in err.message
        assert "abc-123" in err.message
        assert err.code == "NOT_FOUND"

    def test_model_not_found_error(self):
        err = ModelNotFoundError("qwen2.5:7b")
        assert "qwen2.5:7b" in err.message

    def test_rate_limit_error(self):
        err = RateLimitExceededError(retry_after=30)
        assert err.retry_after == 30
        assert err.code == "RATE_LIMIT_EXCEEDED"

    def test_validation_error_with_details(self):
        errors = [{"field": "email", "message": "Required", "code": "required"}]
        err = ValidationError("Invalid input", errors=errors)
        assert len(err.errors) == 1
        assert err.errors[0]["field"] == "email"

    def test_conflict_error(self):
        err = ConflictError("Email already exists")
        assert err.code == "CONFLICT"


class TestTypes:
    def test_auth_context_immutable(self):
        ctx = AuthContext(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="test@example.com",
            roles=["admin"],
        )
        assert ctx.email == "test@example.com"
        with pytest.raises(AttributeError):
            ctx.email = "new@example.com"  # type: ignore

    def test_token_pair(self):
        tp = TokenPair(access_token="abc", refresh_token="def")
        assert tp.token_type == "bearer"
        assert tp.expires_in == 3600

    def test_chat_message(self):
        msg = ChatMessage(role=MessageRole.USER, content="Hello!")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello!"

    def test_model_info(self):
        info = ModelInfo(
            id="qwen2.5:7b",
            name="Qwen 2.5",
            family="qwen",
            parameters="7B",
            runtime=ModelRuntime.OLLAMA,
        )
        assert info.id == "qwen2.5:7b"
        assert info.runtime == ModelRuntime.OLLAMA
        assert info.status == ModelStatus.AVAILABLE

    def test_completion_chunk(self):
        chunk = CompletionChunk(
            id="msg_001",
            content="Hello",
            model="qwen2.5:7b",
        )
        assert chunk.finish_reason is None
        assert chunk.total_tokens is None
