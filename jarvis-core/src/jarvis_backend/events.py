from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

EventType = Literal[
    "user_input",
    "transcription",
    "ai_response_delta",
    "ai_response",
    "system_state",
    "action_confirmation",
    "action_result",
    "audio_level",
    "error",
]


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[Any] = set()

    def subscribe(self, queue: Any) -> None:
        self._subscribers.add(queue)

    def unsubscribe(self, queue: Any) -> None:
        self._subscribers.discard(queue)

    async def publish(self, event_type: EventType, payload: dict[str, Any] | None = None) -> Event:
        event = Event(type=event_type, payload=payload or {})
        stale: list[Any] = []
        for queue in self._subscribers:
            try:
                await queue.put(event)
            except RuntimeError:
                stale.append(queue)
        for queue in stale:
            self.unsubscribe(queue)
        return event
