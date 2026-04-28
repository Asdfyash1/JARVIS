from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from jarvis_backend.state.models import AgentAction


class ActionResult(BaseModel):
    action_id: str
    ok: bool
    message: str
    data: dict[str, str] = Field(default_factory=dict)


class ActionExecutor(ABC):
    @abstractmethod
    async def execute(self, action: AgentAction) -> ActionResult:
        raise NotImplementedError
