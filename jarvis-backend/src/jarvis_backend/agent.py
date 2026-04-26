from __future__ import annotations

import asyncio

from jarvis_backend.actions.manager import ActionManager
from jarvis_backend.audio.output import AudioPlayer
from jarvis_backend.events import EventBus
from jarvis_backend.llm.action_parser import ActionParser
from jarvis_backend.llm.client import NvidiaLlmClient
from jarvis_backend.memory.store import ConversationMemory
from jarvis_backend.state.models import AssistantState, ChatMessage, ChatRole
from jarvis_backend.state.store import StateStore
from jarvis_backend.tts.base import TextToSpeech


class JarvisAgent:
    def __init__(
        self,
        event_bus: EventBus,
        state: StateStore,
        memory: ConversationMemory,
        llm: NvidiaLlmClient,
        parser: ActionParser,
        tts: TextToSpeech,
        player: AudioPlayer,
        actions: ActionManager,
    ) -> None:
        self._event_bus = event_bus
        self._state = state
        self._memory = memory
        self._llm = llm
        self._parser = parser
        self._tts = tts
        self._player = player
        self._actions = actions
        self._current_response_task: asyncio.Task[None] | None = None

    async def handle_user_text(self, text: str, speak: bool = True) -> None:
        text = text.strip()
        if not text:
            return
        await self.interrupt()
        await self._memory.append(ChatMessage(role=ChatRole.USER, content=text))
        await self._event_bus.publish("user_input", {"text": text})
        await self._state.set_state(AssistantState.THINKING)
        self._current_response_task = asyncio.create_task(self._respond(text, speak=speak))

    async def interrupt(self) -> None:
        await self._player.stop()
        if self._current_response_task and not self._current_response_task.done():
            self._current_response_task.cancel()
            try:
                await self._current_response_task
            except asyncio.CancelledError:
                pass

    async def _respond(self, text: str, speak: bool) -> None:
        chunks: list[str] = []
        try:
            history = await self._memory.history()
            async for delta in self._llm.stream(history, text):
                chunks.append(delta)
                await self._event_bus.publish("ai_response_delta", {"delta": delta})
            full_text = "".join(chunks).strip()
            decision = self._parser.parse(full_text)
            await self._memory.append(ChatMessage(role=ChatRole.ASSISTANT, content=decision.spoken_response))
            await self._event_bus.publish(
                "ai_response",
                {
                    "text": decision.spoken_response,
                    "actions": [action.model_dump(mode="json") for action in decision.actions],
                },
            )
            if speak and decision.spoken_response:
                await self._state.set_state(AssistantState.SPEAKING)
                audio_path = await self._tts.synthesize(decision.spoken_response)
                await self._player.play_wav(audio_path)
            for action in decision.actions:
                asyncio.create_task(self._actions.execute_after_confirmation(action))
            await self._state.set_state(AssistantState.IDLE)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self._event_bus.publish("error", {"message": str(exc)})
            await self._state.set_state(AssistantState.ERROR, str(exc))
