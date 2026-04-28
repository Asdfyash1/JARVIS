from __future__ import annotations

import asyncio

from jarvis_backend.actions.base import ActionResult
from jarvis_backend.actions.browser import BrowserActionExecutor
from jarvis_backend.actions.system import SystemActionExecutor
from jarvis_backend.config import ActionsConfig
from jarvis_backend.events import EventBus
from jarvis_backend.state.models import AgentAction, AssistantState, ConfirmationRequest
from jarvis_backend.state.store import StateStore


class ActionManager:
    def __init__(self, config: ActionsConfig, event_bus: EventBus, state: StateStore) -> None:
        self._config = config
        self._event_bus = event_bus
        self._state = state
        self._system = SystemActionExecutor(config)
        self._browser = BrowserActionExecutor(config)
        self._pending: dict[str, AgentAction] = {}
        self._confirmations: dict[str, asyncio.Future[bool]] = {}

    async def request_confirmation(self, action: AgentAction) -> ConfirmationRequest:
        self._pending[action.id] = action
        request = ConfirmationRequest(action=action, prompt=self._prompt(action))
        self._confirmations[action.id] = asyncio.get_running_loop().create_future()
        await self._state.set_state(AssistantState.AWAITING_CONFIRMATION, request.prompt)
        await self._event_bus.publish("action_confirmation", request.model_dump(mode="json"))
        return request

    async def approve(self, action_id: str, approved: bool) -> None:
        future = self._confirmations.get(action_id)
        if future and not future.done():
            future.set_result(approved)

    async def execute_after_confirmation(self, action: AgentAction) -> ActionResult:
        try:
            if self._config.require_confirmation or action.requires_confirmation:
                await self.request_confirmation(action)
                approved = await self._confirmations[action.id]
                self._confirmations.pop(action.id, None)
                if not approved:
                    result = ActionResult(action_id=action.id, ok=False, message="Action cancelled")
                    await self._event_bus.publish("action_result", result.model_dump())
                    await self._state.set_state(AssistantState.IDLE)
                    return result
            await self._state.set_state(AssistantState.EXECUTING_ACTION, action.action)
            executor = self._browser if action.action in self._browser_actions() else self._system
            result = await executor.execute(action)
        except Exception as exc:
            result = ActionResult(action_id=action.id, ok=False, message=str(exc))
        await self._event_bus.publish("action_result", result.model_dump())
        await self._state.set_state(AssistantState.IDLE)
        return result

    @staticmethod
    def _browser_actions() -> set[str]:
        return {"open_website", "google_search", "youtube_control", "whatsapp_message"}

    @staticmethod
    def _prompt(action: AgentAction) -> str:
        if action.action == "open_app":
            return f"Open {action.app_name}?"
        if action.action == "whatsapp_message":
            if action.phone_number:
                return f"Prepare WhatsApp message to {action.phone_number}: {action.message!r}?"
            if not action.contact:
                return f"Send WhatsApp message in the currently open chat: {action.message!r}?"
            return f"Send WhatsApp message to {action.contact}: {action.message!r}?"
        if action.action == "open_website":
            return f"Open {action.url}?"
        if action.action == "google_search":
            return f"Search Google for {action.query!r}?"
        return f"Execute {action.action}?"
