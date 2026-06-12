"""
OmniSLM Application Class.

The primary entry point for the OmniSLM framework.
Provides a fluent API for composing AI applications.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any, Callable

from omnislm.core.config import OmniSLMConfig
from omnislm.core.container import Container
from omnislm.core.events.bus import EventBus
from omnislm.core.interfaces.plugin import BasePlugin
from omnislm.core.interfaces.runtime import BaseRuntime

logger = logging.getLogger("omnislm")


class OmniSLM:
    """The main OmniSLM framework entry point.

    Provides a fluent builder API for composing AI applications
    with runtimes, memory, RAG, agents, plugins, and more.

    Usage:
        # Programmatic configuration
        app = OmniSLM(name="My AI App", debug=True)
        app.enable_memory()
        app.enable_rag()
        app.enable_agents()
        app.install_plugin("calculator")
        app.run()

        # Configuration file
        app = OmniSLM.from_config("omnislm.yaml")
        app.run()

        # ASGI deployment
        app = OmniSLM.from_config("omnislm.yaml")
        fastapi_app = app.build()  # Use with gunicorn/uvicorn
    """

    def __init__(
        self,
        config: OmniSLMConfig | dict[str, Any] | None = None,
        *,
        name: str = "OmniSLM App",
        version: str = "0.1.0",
        debug: bool = False,
    ) -> None:
        # Resolve configuration
        if isinstance(config, dict):
            config = OmniSLMConfig.from_dict(config)
        elif config is None:
            config = OmniSLMConfig(name=name, version=version, debug=debug)

        self._config = config
        self._container = Container(config)
        self._features: set[str] = set()
        self._custom_routers: list[tuple[Any, str, dict[str, Any]]] = []
        self._startup_hooks: list[Callable] = []
        self._shutdown_hooks: list[Callable] = []

        # Setup structured logging
        self._setup_logging()

    # ---- Factory Methods ----

    @classmethod
    def from_config(cls, path: str | Path) -> "OmniSLM":
        """Create an OmniSLM instance from a YAML configuration file.

        Args:
            path: Path to omnislm.yaml.

        Returns:
            Configured OmniSLM instance with features enabled per config.
        """
        config = OmniSLMConfig.from_yaml(path)
        instance = cls(config=config)

        # Auto-enable features based on config
        if config.auth.enabled:
            instance.enable_auth()
        if config.memory.enabled:
            instance.enable_memory()
        if config.rag.enabled:
            instance.enable_rag()
        if config.agents.enabled:
            instance.enable_agents()

        # Auto-load configured plugins
        for plugin_config in config.plugins:
            if plugin_config.enabled:
                instance._features.add(f"plugin:{plugin_config.name}")

        return instance

    # ---- Feature Toggles (Fluent API) ----

    def enable_auth(self, **kwargs: Any) -> "OmniSLM":
        """Enable authentication (JWT, API Key, OAuth2)."""
        self._features.add("auth")
        return self

    def enable_memory(self, *, backend: str | None = None, **kwargs: Any) -> "OmniSLM":
        """Enable the memory subsystem.

        Args:
            backend: Memory backend ('redis', 'sqlite', 'in_memory'). Default from config.
        """
        self._features.add("memory")
        if backend:
            self._config.memory.backend = backend
        return self

    def enable_rag(
        self, *, vector_store: str | None = None, **kwargs: Any
    ) -> "OmniSLM":
        """Enable the RAG pipeline.

        Args:
            vector_store: Vector store backend ('qdrant', 'chroma', 'faiss'). Default from config.
        """
        self._features.add("rag")
        if vector_store:
            self._config.rag.vector_store = vector_store
        return self

    def enable_agents(
        self, *, strategy: str | None = None, **kwargs: Any
    ) -> "OmniSLM":
        """Enable the agent framework.

        Args:
            strategy: Agent strategy ('react', 'function_calling'). Default from config.
        """
        self._features.add("agents")
        if strategy:
            self._config.agents.default_strategy = strategy
        return self

    def enable_workflows(self) -> "OmniSLM":
        """Enable the workflow/DAG engine."""
        self._features.add("workflows")
        return self

    def enable_observability(
        self, *, metrics: bool = True, tracing: bool = False
    ) -> "OmniSLM":
        """Enable Prometheus metrics and/or OpenTelemetry tracing."""
        self._features.add("observability")
        self._config.observability.metrics = metrics
        self._config.observability.tracing = tracing
        return self

    # ---- Runtime Management ----

    def add_runtime(self, name: str, runtime: BaseRuntime) -> "OmniSLM":
        """Register a custom runtime instance.

        Args:
            name: Runtime identifier (e.g., 'ollama', 'vllm', 'my_runtime').
            runtime: A BaseRuntime implementation instance.
        """
        self._container.runtime_registry.register_instance(name, runtime)
        return self

    def set_default_runtime(self, name: str) -> "OmniSLM":
        """Set the default LLM runtime.

        Args:
            name: The name of a previously registered runtime.
        """
        self._config.runtime.default = name
        return self

    # ---- Plugin System ----

    def install_plugin(self, name: str, **config: Any) -> "OmniSLM":
        """Install and activate a plugin by name.

        The plugin is discovered via Python entry_points or
        the local plugins directory.

        Args:
            name: Plugin name (e.g., 'gmail', 'github', 'calculator').
            **config: Plugin-specific configuration.
        """
        self._features.add(f"plugin:{name}")
        # Plugin will be loaded during build()
        return self

    def register_plugin(self, plugin: BasePlugin) -> "OmniSLM":
        """Register a custom plugin instance directly.

        Args:
            plugin: A BasePlugin implementation instance.
        """
        self._container.plugin_registry.register_instance(plugin.name, plugin)
        self._features.add(f"plugin:{plugin.name}")
        return self

    # ---- Event System ----

    def on(self, event_type: str, handler: Callable) -> "OmniSLM":
        """Subscribe to framework events.

        Args:
            event_type: Event type string (e.g., 'document.ingested').
                        Use '*' for all events.
            handler: Async or sync callable.
        """
        self._container.event_bus.subscribe(event_type, handler)
        return self

    # ---- Routes / API Extension ----

    def include_router(self, router: Any, prefix: str = "", **kwargs: Any) -> "OmniSLM":
        """Add custom FastAPI routes to the application.

        Args:
            router: A FastAPI APIRouter instance.
            prefix: URL prefix for the router.
        """
        self._custom_routers.append((router, prefix, kwargs))
        return self

    # ---- Lifecycle Hooks ----

    def on_startup(self, hook: Callable) -> "OmniSLM":
        """Register a startup hook (called after initialization)."""
        self._startup_hooks.append(hook)
        return self

    def on_shutdown(self, hook: Callable) -> "OmniSLM":
        """Register a shutdown hook (called before cleanup)."""
        self._shutdown_hooks.append(hook)
        return self

    # ---- Build & Run ----

    def build(self) -> Any:
        """Build and return the FastAPI application.

        Use this for ASGI deployment (gunicorn, uvicorn, etc.)
        without calling run().

        Returns:
            A configured FastAPI application instance.
        """
        from fastapi import FastAPI

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            # ---- Startup ----
            logger.info(
                "OmniSLM starting: %s v%s [%s]",
                self._config.name,
                self._config.version,
                self._config.environment,
            )

            await self._container.initialize()

            for hook in self._startup_hooks:
                if callable(hook):
                    result = hook()
                    if hasattr(result, "__await__"):
                        await result

            yield

            # ---- Shutdown ----
            for hook in self._shutdown_hooks:
                if callable(hook):
                    result = hook()
                    if hasattr(result, "__await__"):
                        await result

            await self._container.shutdown()
            logger.info("OmniSLM shut down gracefully")

        app = FastAPI(
            title=self._config.name,
            description=(
                "Built with OmniSLM — The open-source AI framework "
                "for Small Language Models."
            ),
            version=self._config.version,
            docs_url="/docs" if self._config.debug else None,
            redoc_url="/redoc" if self._config.debug else None,
            lifespan=lifespan,
        )

        # Wire features
        self._wire_middleware(app)
        self._wire_health_routes(app)

        if "auth" in self._features:
            self._wire_auth(app)

        if "observability" in self._features:
            self._wire_observability(app)

        # Wire custom routers
        for router, prefix, kwargs in self._custom_routers:
            app.include_router(router, prefix=prefix, **kwargs)

        # Store container on app state for dependency injection
        app.state.omnislm = self
        app.state.container = self._container
        app.state.config = self._config

        return app

    def run(
        self,
        host: str | None = None,
        port: int | None = None,
        *,
        reload: bool = False,
        workers: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Start the application server.

        Args:
            host: Bind host. Default from config.
            port: Bind port. Default from config.
            reload: Enable auto-reload for development.
            workers: Number of worker processes.
        """
        import uvicorn

        app = self.build()

        uvicorn.run(
            app,
            host=host or self._config.host,
            port=port or self._config.port,
            reload=reload,
            workers=workers or self._config.workers,
            log_level=self._config.observability.log_level.lower(),
            **kwargs,
        )

    # ---- Properties ----

    @property
    def config(self) -> OmniSLMConfig:
        """Access the configuration."""
        return self._config

    @property
    def container(self) -> Container:
        """Access the DI container."""
        return self._container

    @property
    def event_bus(self) -> EventBus:
        """Access the event bus."""
        return self._container.event_bus

    @property
    def features(self) -> set[str]:
        """Return enabled features."""
        return self._features.copy()

    # ---- Private Methods ----

    def _setup_logging(self) -> None:
        """Configure structured logging based on config."""
        import structlog

        log_level = self._config.observability.log_level.upper()
        json_output = self._config.observability.log_format == "json"

        shared_processors: list[structlog.types.Processor] = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
        ]

        renderer: structlog.types.Processor
        if json_output:
            renderer = structlog.processors.JSONRenderer()
        else:
            renderer = structlog.dev.ConsoleRenderer(colors=True)

        structlog.configure(
            processors=[
                *shared_processors,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )

        import sys

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(getattr(logging, log_level))

        # Suppress noisy loggers
        for name in ("uvicorn.access", "httpx", "httpcore"):
            logging.getLogger(name).setLevel(logging.WARNING)

    def _wire_middleware(self, app: Any) -> None:
        """Set up CORS and request context middleware."""
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=self._config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID"],
        )

    def _wire_health_routes(self, app: Any) -> None:
        """Add health check endpoints."""
        from fastapi import APIRouter

        router = APIRouter(tags=["Health"])

        @router.get("/healthz", summary="Liveness probe")
        async def liveness() -> dict:
            return {
                "status": "alive",
                "name": self._config.name,
                "version": self._config.version,
                "features": sorted(self._features),
            }

        @router.get("/readyz", summary="Readiness probe")
        async def readiness() -> dict:
            checks: dict[str, Any] = {}

            for key, runtime in self._container.runtime_registry.list_instances().items():
                try:
                    available = await runtime.is_available()
                    checks[key] = {"status": "healthy" if available else "unhealthy"}
                except Exception as e:
                    checks[key] = {"status": "unhealthy", "error": str(e)}

            all_healthy = all(
                c.get("status") == "healthy" for c in checks.values()
            )

            return {
                "status": "ready" if all_healthy else "not_ready",
                "version": self._config.version,
                "checks": checks,
            }

        app.include_router(router)

    def _wire_auth(self, app: Any) -> None:
        """Wire authentication middleware and routes."""
        # Auth is wired through the api-server app, not the SDK itself.
        # The SDK provides the container; apps provide the auth implementation.
        pass

    def _wire_observability(self, app: Any) -> None:
        """Wire metrics and tracing."""
        if self._config.observability.metrics:
            try:
                from prometheus_fastapi_instrumentator import Instrumentator

                Instrumentator(
                    should_group_status_codes=False,
                    should_ignore_untemplated=True,
                    excluded_handlers=["/healthz", "/readyz", "/metrics"],
                ).instrument(app).expose(app, include_in_schema=False)
            except ImportError:
                logger.warning(
                    "prometheus-fastapi-instrumentator not installed, "
                    "metrics disabled"
                )
