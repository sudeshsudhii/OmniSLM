"""
OmniSLM Core Domain Exceptions.

Hierarchical exception classes for clean error handling across layers.
"""

from __future__ import annotations


class OmniSLMError(Exception):
    """Base exception for all OmniSLM errors."""

    def __init__(self, message: str = "An unexpected error occurred", code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# ---- Authentication & Authorization ----

class AuthenticationError(OmniSLMError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(OmniSLMError):
    """Raised when a user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class InvalidTokenError(AuthenticationError):
    """Raised when a JWT or API key is invalid."""

    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message=message)
        self.code = "INVALID_TOKEN"


# ---- Resource Errors ----

class NotFoundError(OmniSLMError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource", resource_id: str | None = None):
        msg = f"{resource} not found"
        if resource_id:
            msg = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=msg, code="NOT_FOUND")


class ConflictError(OmniSLMError):
    """Raised when a resource already exists or conflicts."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, code="CONFLICT")


class ValidationError(OmniSLMError):
    """Raised when input validation fails at the domain level."""

    def __init__(self, message: str = "Validation error", errors: list[dict] | None = None):
        super().__init__(message=message, code="VALIDATION_ERROR")
        self.errors = errors or []


# ---- Model & Inference Errors ----

class ModelError(OmniSLMError):
    """Base error for model-related issues."""

    def __init__(self, message: str = "Model error"):
        super().__init__(message=message, code="MODEL_ERROR")


class ModelNotFoundError(ModelError):
    """Raised when a requested model is not available."""

    def __init__(self, model_id: str):
        super().__init__(message=f"Model '{model_id}' not found or not loaded")
        self.code = "MODEL_NOT_FOUND"


class ModelInferenceError(ModelError):
    """Raised when model inference fails."""

    def __init__(self, message: str = "Model inference failed"):
        super().__init__(message=message)
        self.code = "INFERENCE_ERROR"


class RuntimeNotAvailableError(ModelError):
    """Raised when a requested runtime is not available."""

    def __init__(self, runtime: str):
        super().__init__(message=f"Runtime '{runtime}' is not available or not configured")
        self.code = "RUNTIME_UNAVAILABLE"


# ---- Rate Limiting ----

class RateLimitExceededError(OmniSLMError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(message="Rate limit exceeded", code="RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after
