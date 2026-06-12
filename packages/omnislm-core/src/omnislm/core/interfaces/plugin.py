"""
OmniSLM Plugin Interface.

Defines the contract for framework plugins — the primary extensibility
mechanism in OmniSLM. Plugins can provide tools, routes, event handlers,
and custom middleware.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable

from omnislm.core.interfaces.tool import BaseTool


class BasePlugin(ABC):
    """Abstract base class for all OmniSLM plugins.

    Plugins are the primary way to extend OmniSLM with new capabilities
    (Gmail, GitHub, Slack, custom databases, etc.).

    Lifecycle:
        1. Discovered (via entry_points or local directory)
        2. Configured (config loaded from omnislm.yaml or passed programmatically)
        3. Initialized (connections established, state set up)
        4. Active (tools and routes registered, events subscribed)
        5. Shutdown (cleanup on app shutdown)

    Example:
        class GmailPlugin(BasePlugin):
            @property
            def name(self) -> str:
                return "gmail"

            @property
            def version(self) -> str:
                return "1.0.0"

            async def initialize(self, config):
                self.client = GmailClient(config["credentials_path"])

            async def shutdown(self):
                await self.client.close()

            def get_tools(self):
                return [GmailSendTool(self.client), GmailReadTool(self.client)]
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier (e.g., 'gmail', 'github')."""

    @property
    @abstractmethod
    def version(self) -> str:
        """SemVer version string."""

    @property
    def description(self) -> str:
        """Human-readable description of the plugin."""
        return ""

    @property
    def dependencies(self) -> list[str]:
        """Other plugins this plugin depends on."""
        return []

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """Called when the plugin is loaded. Set up connections, state, etc.

        Args:
            config: Plugin configuration from omnislm.yaml or install_plugin().
        """

    @abstractmethod
    async def shutdown(self) -> None:
        """Called on app shutdown. Clean up resources."""

    def get_tools(self) -> list[BaseTool]:
        """Return tools this plugin provides to agents.

        Override to expose tools that agents can invoke.
        """
        return []

    def get_routes(self) -> list[Any]:
        """Return API routers this plugin exposes.

        Override to add custom API endpoints.
        Returns a list of FastAPI APIRouter instances.
        """
        return []

    def get_event_handlers(self) -> dict[str, list[Callable]]:
        """Return event handlers this plugin subscribes to.

        Override to react to framework events.
        Returns a dict mapping event_type -> list of handler callables.
        """
        return {}

    def get_middleware(self) -> list[Any]:
        """Return middleware this plugin provides.

        Override to add custom request/response processing.
        """
        return []
