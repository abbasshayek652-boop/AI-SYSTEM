from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Event:
    topic: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InMemoryEventBus:
    """Development event bus with a stable interface for a future Pub/Sub adapter."""

    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[Event]]] = {}

    def subscribe(self, topic: str) -> asyncio.Queue[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue()
        self._queues.setdefault(topic, []).append(queue)
        return queue

    async def publish(self, event: Event) -> int:
        queues = list(self._queues.get(event.topic, []))
        for queue in queues:
            await queue.put(event)
        return len(queues)

    def subscriber_count(self, topic: str | None = None) -> int:
        if topic is not None:
            return len(self._queues.get(topic, []))
        return sum(len(queues) for queues in self._queues.values())
