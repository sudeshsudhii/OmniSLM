"""
OmniSLM Event Bus.

Simple in-memory pub/sub mechanism for decoupling domain logic.
"""

import asyncio
from collections import defaultdict
from typing import Callable

from src.config.logging import get_logger
from src.core.events.models import DomainEvent

logger = get_logger(__name__)

# Type for event handlers
EventHandler = Callable[[DomainEvent], Any]


class EventBus:
    """In-memory event bus for publishing and subscribing to events."""

    def __init__(self):
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type."""
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type}")

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers."""
        handlers = self._subscribers.get(event.event_type, [])
        if not handlers:
            return

        logger.debug(f"Publishing event {event.event_type} to {len(handlers)} handlers")
        
        for handler in handlers:
            try:
                import inspect
                if inspect.iscoroutinefunction(handler):
                    # Fire and forget (don't await directly to avoid blocking)
                    # In a production system, these might be enqueued in Celery or handled differently
                    asyncio.create_task(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event.event_type}", error=str(e))


# Global event bus
event_bus = EventBus()
