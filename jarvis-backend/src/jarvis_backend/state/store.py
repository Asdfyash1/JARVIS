from __future__ import annotations

import asyncio

from jarvis_backend.events import EventBus
from jarvis_backend.state.models import AssistantState


class StateStore:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._state = AssistantState.IDLE
        self._lock = asyncio.Lock()

    @property
    def state(self) -> AssistantState:
        return self._state

    async def set_state(self, state: AssistantState, detail: str | None = None) -> None:
        async with self._lock:
            self._state = state
            await self._event_bus.publish(
                "system_state",
                {"state": state.value, "detail": detail},
            )
