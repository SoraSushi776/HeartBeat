"""In-process publish subscribe bus for SSE streaming."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

SUBSCRIBER_QUEUE_SIZE = 64


@dataclass(frozen=True)
class StreamEvent:
    """One server-sent event payload."""

    event: str
    data: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Singleton fan-out bus delivering StreamEvent to SSE subscribers."""

    _instance: EventBus | None = None

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[StreamEvent]] = []

    @classmethod
    def instance(cls) -> EventBus:
        """Return the process-wide bus singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Drop the cached bus singleton."""
        cls._instance = None

    def subscribe(self) -> asyncio.Queue[StreamEvent]:
        """Register a subscriber queue for SSE delivery."""
        queue: asyncio.Queue[StreamEvent] = asyncio.Queue(maxsize=SUBSCRIBER_QUEUE_SIZE)
        self._subscribers.append(queue)
        logger.debug("SSE subscriber added: total=%d", len(self._subscribers))
        return queue

    def unsubscribe(self, queue: asyncio.Queue[StreamEvent]) -> None:
        """Remove a subscriber queue registered earlier."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)
            logger.debug("SSE subscriber removed: total=%d", len(self._subscribers))

    def publish(self, item: StreamEvent) -> None:
        """Deliver an event to every subscriber without blocking the caller."""
        for queue in list(self._subscribers):
            self._offer(queue, item)

    def _offer(self, queue: asyncio.Queue[StreamEvent], item: StreamEvent) -> None:
        """Push an event into one queue, dropping the oldest when full."""
        try:
            queue.put_nowait(item)
        except asyncio.QueueFull:
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                queue.put_nowait(item)
            except asyncio.QueueFull:
                logger.warning("SSE subscriber queue still full, event dropped")
