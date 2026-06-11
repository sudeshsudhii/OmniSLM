"""
OmniSLM API Middleware.

Request ID injection, CORS, rate limiting, and global error handling.
"""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.constants import RATE_LIMIT_WINDOW_SECONDS
from src.config.settings import get_settings
from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ModelError,
    NotFoundError,
    OmniSLMError,
    RateLimitExceededError,
    ValidationError,
)
from src.infrastructure.cache.redis_client import redis_client

settings = get_settings()


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI app."""

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # Request ID + Logging + Timing
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next) -> Response:
        """Inject request ID, bind structured logging context, and measure timing."""
        request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        request.state.request_id = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        logger = structlog.get_logger()
        await logger.ainfo(
            "Request completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response

    # Rate Limiting (token bucket via Redis)
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next) -> Response:
        """Per-IP rate limiting using Redis sliding window."""
        # Skip health checks
        if request.url.path in ("/healthz", "/readyz", "/docs", "/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        rate_key = f"ratelimit:{client_ip}"

        try:
            current = await redis_client.incr(rate_key)
            if current == 1:
                await redis_client.expire(rate_key, RATE_LIMIT_WINDOW_SECONDS)

            ttl = await redis_client.ttl(rate_key)
            limit = settings.rate_limit_per_minute
            remaining = max(0, limit - current)

            if current > limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": ttl,
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(ttl),
                        "Retry-After": str(ttl),
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response

        except Exception:
            # If Redis is down, allow the request (fail-open)
            return await call_next(request)

    # Global Exception Handlers
    @app.exception_handler(OmniSLMError)
    async def omnislm_error_handler(request: Request, exc: OmniSLMError) -> JSONResponse:
        """Map domain exceptions to HTTP responses."""
        status_map = {
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            NotFoundError: status.HTTP_404_NOT_FOUND,
            ConflictError: status.HTTP_409_CONFLICT,
            ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
            RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
            ModelError: status.HTTP_502_BAD_GATEWAY,
        }

        http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        for exc_type, code in status_map.items():
            if isinstance(exc, exc_type):
                http_status = code
                break

        body = {
            "title": exc.code.replace("_", " ").title(),
            "status": http_status,
            "detail": exc.message,
            "request_id": getattr(request.state, "request_id", None),
        }

        if isinstance(exc, ValidationError) and exc.errors:
            body["errors"] = exc.errors

        if isinstance(exc, RateLimitExceededError):
            return JSONResponse(
                status_code=http_status,
                content=body,
                headers={"Retry-After": str(exc.retry_after)},
            )

        return JSONResponse(status_code=http_status, content=body)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions."""
        logger = structlog.get_logger()
        await logger.aerror("Unhandled exception", error=str(exc), exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred" if settings.is_production else str(exc),
                "request_id": getattr(request.state, "request_id", None),
            },
        )
