"""
In-process event bus with publish/subscribe and optional persistence.
"""
import structlog
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.events.schemas import PlatformEvent

logger = structlog.get_logger()

# Type alias for event handlers
EventHandler = Callable[[PlatformEvent], Coroutine[Any, Any, None]]


class EventBus:
    """
    In-process event bus.

    Supports:
    - Publish events (with optional DB persistence)
    - Subscribe handlers by event_type pattern (exact match or wildcard prefix)
    - Wildcard subscriptions: "health.*" matches "health.meal_logged", etc.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._global_handlers: list[EventHandler] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type or pattern."""
        self._handlers[event_type].append(handler)
        logger.debug("event_handler_subscribed", event_type=event_type, handler=handler.__name__)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe a handler to ALL events."""
        self._global_handlers.append(handler)

    async def publish(
        self,
        event: PlatformEvent,
        session: AsyncSession | None = None,
    ) -> None:
        """
        Publish an event. Optionally persists to the database.
        Dispatches to all matching handlers.
        """
        logger.info(
            "event_published",
            event_type=event.event_type,
            event_id=str(event.id),
            correlation_id=str(event.correlation_id) if event.correlation_id else None,
        )

        # Persist to database if session provided
        if session is not None:
            from src.events.repository import EventRepository
            repo = EventRepository(session)
            await repo.persist(event)

        # Dispatch to matching handlers
        await self._dispatch(event)

    async def _dispatch(self, event: PlatformEvent) -> None:
        """Dispatch event to all matching handlers."""
        handlers_to_call: list[EventHandler] = []

        # Exact match handlers
        if event.event_type in self._handlers:
            handlers_to_call.extend(self._handlers[event.event_type])

        # Wildcard prefix match (e.g., "health.*" matches "health.meal_logged")
        for pattern, handlers in self._handlers.items():
            if pattern.endswith(".*"):
                prefix = pattern[:-2]
                if event.event_type.startswith(prefix + ".") and pattern != event.event_type:
                    handlers_to_call.extend(handlers)

        # Global handlers
        handlers_to_call.extend(self._global_handlers)

        # Execute all handlers
        for handler in handlers_to_call:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "event_handler_error",
                    event_type=event.event_type,
                    handler=handler.__name__,
                )


# Singleton event bus instance
event_bus = EventBus()
