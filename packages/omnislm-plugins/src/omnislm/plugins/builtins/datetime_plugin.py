"""
Built-in DateTime Plugin.

Provides current date/time information to agents.
"""

from datetime import datetime, timezone
from typing import Any

from omnislm.core.interfaces.plugin import BasePlugin
from omnislm.core.interfaces.tool import BaseTool


class DateTimeTool(BaseTool):
    """Returns current date and time."""

    name = "datetime"
    description = "Get the current date and time. No input needed."

    async def execute(self, **kwargs: Any) -> str:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d %H:%M:%S UTC")


class DateTimePlugin(BasePlugin):
    """DateTime plugin providing time-related tools."""

    @property
    def name(self) -> str:
        return "datetime"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Get current date and time"

    async def initialize(self, config: dict[str, Any]) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def get_tools(self) -> list[BaseTool]:
        return [DateTimeTool()]
