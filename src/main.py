"""
OmniSLM — Main Application Entry Point.

Creates and configures the FastAPI application with all routes,
middleware, and lifecycle events.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from src.api.middleware import setup_middleware
from src.api.routes.auth import router as auth_router
from src.api.routes.chat import chat_router, conversation_router
from src.api.routes.health import router as health_router
from src.api.routes.models import router as models_router
from src.config.constants import API_V1_PREFIX
from src.config.logging import setup_logging
from src.config.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle: startup and shutdown events."""
    # ---- Startup ----
    setup_logging(
        log_level=settings.log_level,
        json_output=settings.is_production,
    )

    import structlog
    logger = structlog.get_logger()
    await logger.ainfo(
        "OmniSLM starting",
        version=settings.app_version,
        environment=settings.environment,
        host=settings.host,
        port=settings.port,
    )

    yield

    # ---- Shutdown ----
    from src.infrastructure.cache.redis_client import redis_client
    await redis_client.aclose()

    from src.core.registry.runtime_registry import runtime_registry
    await runtime_registry.close_all()

    await logger.ainfo("OmniSLM shut down gracefully")


def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI application."""
    app = FastAPI(
        title="OmniSLM",
        description=(
            "The open-source AI framework for Small Language Models. "
            "Build AI assistants, RAG applications, and autonomous agents "
            "using local or self-hosted models."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware
    setup_middleware(app)

    # Telemetry (Tracing & Metrics)
    from src.infrastructure.telemetry import setup_metrics, setup_tracing
    setup_tracing(app)
    setup_metrics(app)

    # Health routes (no prefix, K8s standard)
    app.include_router(health_router)

    # API v1 routes
    app.include_router(auth_router, prefix=API_V1_PREFIX)
    app.include_router(models_router, prefix=API_V1_PREFIX)
    app.include_router(chat_router, prefix=API_V1_PREFIX)
    app.include_router(conversation_router, prefix=API_V1_PREFIX)

    return app


# Application instance used by uvicorn
app = create_app()
