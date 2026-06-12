"""
OmniSLM Reference API Server.

This is the reference implementation of a full-featured AI application
built on top of the OmniSLM framework. It demonstrates how to use the
framework to build a production-grade API server with:

- JWT authentication + multi-tenant support
- Chat completions (streaming and non-streaming)
- Model management (list, pull, info)
- Health checks (liveness + readiness)
- Conversation history (PostgreSQL)
- Rate limiting and CORS

This file replaces the original src/main.py by using the OmniSLM SDK.
"""

from __future__ import annotations

import logging
from pathlib import Path

from omnislm import OmniSLM
from omnislm.runtimes import OllamaRuntime

logger = logging.getLogger(__name__)


def create_app() -> OmniSLM:
    """Create and configure the OmniSLM API server.

    This factory function builds the full application, wiring together
    the framework's features with app-specific routes and services.

    Returns:
        A configured OmniSLM instance ready to run.
    """
    # Load config from YAML if available, otherwise use defaults
    config_path = Path("omnislm.yaml")
    if config_path.exists():
        app = OmniSLM.from_config(config_path)
    else:
        app = OmniSLM(
            name="OmniSLM API Server",
            version="0.1.0",
            debug=True,
        )

    # Enable framework features
    app.enable_auth()
    app.enable_memory()
    app.enable_observability(metrics=True, tracing=False)

    # Register the default runtime
    ollama = OllamaRuntime(
        base_url=app.config.runtime.ollama_base_url,
    )
    app.add_runtime("ollama", ollama)
    app.set_default_runtime("ollama")

    # Register built-in plugins
    app.install_plugin("calculator")
    app.install_plugin("datetime")

    # Wire app-specific routes
    # These routes use app-level services (auth, chat, models)
    # that are NOT part of the framework — they are app-specific logic.
    #
    # from app.routes import auth, chat, models
    # app.include_router(auth.router, prefix="/api/v1")
    # app.include_router(chat.router, prefix="/api/v1")
    # app.include_router(models.router, prefix="/api/v1")

    # Lifecycle hooks
    @app.on_startup
    async def on_startup():
        logger.info("API Server started — ready to accept requests")

    @app.on_shutdown
    async def on_shutdown():
        logger.info("API Server shutting down")

    return app


# Create the app instance
app = create_app()

# For ASGI deployment (gunicorn / uvicorn):
#   uvicorn apps.api_server.main:asgi_app --host 0.0.0.0 --port 8000
asgi_app = app.build()

if __name__ == "__main__":
    app.run(port=8000, reload=True)
