"""
OmniSLM Event Bus.

Instance-based pub/sub mechanism for decoupling domain logic.
No global singletons — each OmniSLM app gets its own EventBus.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable

from omnislm.core.events.models import DomainEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[DomainEvent], Any]


class EventBus:
    """In-memory event bus for publishing and subscribing to events.

    Each OmniSLM application instance creates its own EventBus,
    avoiding global state and enabling proper isolation.

    Example:
        bus = EventBus()
        bus.subscribe("user.registered", handle_registration)
        await bus.publish(UserRegisteredEvent(user_id="123"))
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._wildcard_subscribers: list[EventHandler] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type.

        Args:
            event_type: The event type string (e.g., 'document.ingested').
                        Use '*' to subscribe to all events.
            handler: Async or sync callable that receives a DomainEvent.
        """
        if event_type == "*":
            self._wildcard_subscribers.append(handler)
        else:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler from an event type."""
        if event_type == "*":
            self._wildcard_subscribers = [
                h for h in self._wildcard_subscribers if h != handler
            ]
        elif event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers.

        Handlers are invoked concurrently. Errors in individual
        handlers are logged but do not prevent other handlers from running.
        """
        handlers = [
            *self._subscribers.get(event.event_type, []),
            *self._wildcard_subscribers,
        ]

        if not handlers:
            return

        logger.debug(
            "Publishing event %s to %d handlers",
            event.event_type,
            len(handlers),
        )

        tasks = []
        for handler in handlers:
            try:
                import inspect

                if inspect.iscoroutinefunction(handler):
                    tasks.append(asyncio.create_task(handler(event)))
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    "Error handling event %s: %s",
                    event.event_type,
                    str(e),
                )

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(
                        "Async handler error for %s: %s",
                        event.event_type,
                        str(result),
                    )

    def clear(self) -> None:
        """Remove all subscribers."""
        self._subscribers.clear()
        self._wildcard_subscribers.clear()
