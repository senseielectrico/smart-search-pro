"""
Event bus for loose coupling between modules.

Provides a publish-subscribe pattern for decoupled communication
between components with support for async handlers, filtering, and priorities.
"""

import asyncio
import inspect
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Coroutine

from .logger import get_logger

logger = get_logger(__name__)


class EventPriority(IntEnum):
    """Event handler priority levels."""

    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


@dataclass
class Event:
    """Base event class."""

    name: str
    data: dict[str, Any]
    timestamp: float
    source: str | None = None
    propagate: bool = True

    def stop_propagation(self) -> None:
        """Stop event propagation to remaining handlers."""
        self.propagate = False


@dataclass
class EventHandler:
    """Event handler metadata."""

    callback: Callable[[Event], Any] | Callable[[Event], Coroutine[Any, Any, None]]
    priority: int
    filter_func: Callable[[Event], bool] | None
    once: bool
    async_handler: bool


class EventBus:
    """
    Thread-safe event bus with pub-sub pattern.

    Features:
    - Synchronous and asynchronous handlers
    - Handler priorities
    - Event filtering
    - One-time handlers
    - Event propagation control
    - Handler statistics
    """

    def __init__(self) -> None:
        """Initialize event bus."""
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = threading.RLock()
        self._event_count: dict[str, int] = defaultdict(int)
        self._handler_count: dict[str, int] = defaultdict(int)
        self._last_event: dict[str, Event] = {}

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[Event], Any] | Callable[[Event], Coroutine[Any, Any, None]],
        priority: int = EventPriority.NORMAL,
        filter_func: Callable[[Event], bool] | None = None,
        once: bool = False,
    ) -> None:
        """
        Subscribe to an event.

        Args:
            event_name: Name of event to subscribe to
            callback: Handler function (sync or async)
            priority: Handler priority (higher = earlier execution)
            filter_func: Optional filter function to selectively handle events
            once: If True, handler is removed after first execution
        """
        is_async = inspect.iscoroutinefunction(callback)

        handler = EventHandler(
            callback=callback,
            priority=priority,
            filter_func=filter_func,
            once=once,
            async_handler=is_async,
        )

        with self._lock:
            self._handlers[event_name].append(handler)
            # Sort by priority (highest first)
            self._handlers[event_name].sort(key=lambda h: h.priority, reverse=True)
            self._handler_count[event_name] += 1

        logger.debug(
            "Subscribed to event",
            event=event_name,
            priority=priority,
            async_handler=is_async,
            once=once,
        )

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[[Event], Any] | Callable[[Event], Coroutine[Any, Any, None]],
    ) -> bool:
        """
        Unsubscribe from an event.

        Args:
            event_name: Name of event to unsubscribe from
            callback: Handler function to remove

        Returns:
            True if handler was removed, False if not found
        """
        with self._lock:
            handlers = self._handlers.get(event_name, [])
            for i, handler in enumerate(handlers):
                if handler.callback == callback:
                    handlers.pop(i)
                    self._handler_count[event_name] -= 1
                    logger.debug("Unsubscribed from event", event=event_name)
                    return True

        return False

    def publish(
        self,
        event_name: str,
        data: dict[str, Any] | None = None,
        source: str | None = None,
    ) -> Event:
        """
        Publish an event synchronously.

        Args:
            event_name: Name of event to publish
            data: Event data
            source: Event source identifier

        Returns:
            Event object
        """
        event = Event(
            name=event_name,
            data=data or {},
            timestamp=time.time(),
            source=source,
        )

        with self._lock:
            self._event_count[event_name] += 1
            self._last_event[event_name] = event
            handlers = list(self._handlers.get(event_name, []))

        logger.debug(
            "Publishing event",
            event=event_name,
            handlers=len(handlers),
            source=source,
        )

        # Execute handlers
        handlers_to_remove = []
        for handler in handlers:
            if not event.propagate:
                break

            # Apply filter if present
            if handler.filter_func and not handler.filter_func(event):
                continue

            try:
                if handler.async_handler:
                    # Schedule async handler
                    asyncio.create_task(handler.callback(event))
                else:
                    # Execute sync handler
                    handler.callback(event)

            except Exception as e:
                logger.error(
                    "Error in event handler",
                    event=event_name,
                    error=str(e),
                    exc_info=True,
                )

            # Mark for removal if one-time handler
            if handler.once:
                handlers_to_remove.append(handler)

        # Remove one-time handlers
        if handlers_to_remove:
            with self._lock:
                for handler in handlers_to_remove:
                    try:
                        self._handlers[event_name].remove(handler)
                        self._handler_count[event_name] -= 1
                    except ValueError:
                        pass

        return event

    async def publish_async(
        self,
        event_name: str,
        data: dict[str, Any] | None = None,
        source: str | None = None,
    ) -> Event:
        """
        Publish an event asynchronously.

        Args:
            event_name: Name of event to publish
            data: Event data
            source: Event source identifier

        Returns:
            Event object
        """
        event = Event(
            name=event_name,
            data=data or {},
            timestamp=time.time(),
            source=source,
        )

        with self._lock:
            self._event_count[event_name] += 1
            self._last_event[event_name] = event
            handlers = list(self._handlers.get(event_name, []))

        logger.debug(
            "Publishing event (async)",
            event=event_name,
            handlers=len(handlers),
            source=source,
        )

        # Execute handlers
        handlers_to_remove = []
        for handler in handlers:
            if not event.propagate:
                break

            # Apply filter if present
            if handler.filter_func and not handler.filter_func(event):
                continue

            try:
                if handler.async_handler:
                    await handler.callback(event)
                else:
                    # Run sync handler in thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, handler.callback, event)

            except Exception as e:
                logger.error(
                    "Error in event handler",
                    event=event_name,
                    error=str(e),
                    exc_info=True,
                )

            # Mark for removal if one-time handler
            if handler.once:
                handlers_to_remove.append(handler)

        # Remove one-time handlers
        if handlers_to_remove:
            with self._lock:
                for handler in handlers_to_remove:
                    try:
                        self._handlers[event_name].remove(handler)
                        self._handler_count[event_name] -= 1
                    except ValueError:
                        pass

        return event

    def clear_handlers(self, event_name: str | None = None) -> None:
        """
        Clear event handlers.

        Args:
            event_name: Event name (None = clear all)
        """
        with self._lock:
            if event_name is None:
                self._handlers.clear()
                self._handler_count.clear()
                logger.info("Cleared all event handlers")
            else:
                self._handlers.pop(event_name, None)
                self._handler_count.pop(event_name, None)
                logger.debug("Cleared event handlers", event=event_name)

    def has_handlers(self, event_name: str) -> bool:
        """
        Check if event has handlers.

        Args:
            event_name: Event name

        Returns:
            True if event has handlers
        """
        with self._lock:
            return bool(self._handlers.get(event_name))

    def get_handler_count(self, event_name: str | None = None) -> int:
        """
        Get number of handlers.

        Args:
            event_name: Event name (None = total for all events)

        Returns:
            Number of handlers
        """
        with self._lock:
            if event_name is None:
                return sum(self._handler_count.values())
            return self._handler_count.get(event_name, 0)

    def get_event_count(self, event_name: str | None = None) -> int:
        """
        Get number of events published.

        Args:
            event_name: Event name (None = total for all events)

        Returns:
            Number of events
        """
        with self._lock:
            if event_name is None:
                return sum(self._event_count.values())
            return self._event_count.get(event_name, 0)

    def get_last_event(self, event_name: str) -> Event | None:
        """
        Get last event published.

        Args:
            event_name: Event name

        Returns:
            Last event or None
        """
        with self._lock:
            return self._last_event.get(event_name)

    def get_stats(self) -> dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                "total_events": sum(self._event_count.values()),
                "total_handlers": sum(self._handler_count.values()),
                "event_counts": dict(self._event_count),
                "handler_counts": dict(self._handler_count),
                "event_types": list(self._handlers.keys()),
            }

    def reset_stats(self) -> None:
        """Reset event statistics."""
        with self._lock:
            self._event_count.clear()
            self._last_event.clear()
            logger.debug("Reset event statistics")


# Decorator for event handlers
def event_handler(
    event_name: str,
    priority: int = EventPriority.NORMAL,
    filter_func: Callable[[Event], bool] | None = None,
    once: bool = False,
    bus: EventBus | None = None,
):
    """
    Decorator to register event handlers.

    Args:
        event_name: Name of event to handle
        priority: Handler priority
        filter_func: Optional filter function
        once: If True, handler is removed after first execution
        bus: EventBus instance (uses global if None)

    Example:
        @event_handler("file.opened")
        def on_file_opened(event: Event):
            print(f"File opened: {event.data['path']}")
    """
    def decorator(func):
        target_bus = bus or get_event_bus()
        target_bus.subscribe(event_name, func, priority, filter_func, once)
        return func
    return decorator


# Global event bus instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    Get global event bus instance.

    Returns:
        EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def publish(
    event_name: str,
    data: dict[str, Any] | None = None,
    source: str | None = None,
) -> Event:
    """
    Publish event to global bus (convenience function).

    Args:
        event_name: Name of event to publish
        data: Event data
        source: Event source identifier

    Returns:
        Event object
    """
    return get_event_bus().publish(event_name, data, source)


async def publish_async(
    event_name: str,
    data: dict[str, Any] | None = None,
    source: str | None = None,
) -> Event:
    """
    Publish event to global bus asynchronously (convenience function).

    Args:
        event_name: Name of event to publish
        data: Event data
        source: Event source identifier

    Returns:
        Event object
    """
    return await get_event_bus().publish_async(event_name, data, source)


def subscribe(
    event_name: str,
    callback: Callable[[Event], Any] | Callable[[Event], Coroutine[Any, Any, None]],
    priority: int = EventPriority.NORMAL,
    filter_func: Callable[[Event], bool] | None = None,
    once: bool = False,
) -> None:
    """
    Subscribe to event on global bus (convenience function).

    Args:
        event_name: Name of event to subscribe to
        callback: Handler function (sync or async)
        priority: Handler priority
        filter_func: Optional filter function
        once: If True, handler is removed after first execution
    """
    get_event_bus().subscribe(event_name, callback, priority, filter_func, once)
