from __future__ import annotations

import asyncio

from jarvis_backend.agent import JarvisAgent
from jarvis_backend.audio.input import MicrophoneStream
from jarvis_backend.audio.vad import UtteranceDetector
from jarvis_backend.events import EventBus
from jarvis_backend.state.models import AssistantState
from jarvis_backend.state.store import StateStore
from jarvis_backend.stt.base import SpeechToText


class VoicePipeline:
    def __init__(
        self,
        microphone: MicrophoneStream,
        detector: UtteranceDetector,
        stt: SpeechToText,
        agent: JarvisAgent,
        event_bus: EventBus,
        state: StateStore,
    ) -> None:
        self._microphone = microphone
        self._detector = detector
        self._stt = stt
        self._agent = agent
        self._event_bus = event_bus
        self._state = state
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        await self._state.set_state(AssistantState.LISTENING)
        async for frame in self._microphone.frames():
            level = float(abs(frame).mean())
            await self._event_bus.publish("audio_level", {"level": level})
            segment = await self._detector.push_frame(frame)
            if segment is None:
                continue
            await self._state.set_state(AssistantState.TRANSCRIBING)
            text = await self._stt.transcribe(segment)
            await self._event_bus.publish("transcription", {"text": text})
            if text:
                await self._agent.handle_user_text(text, speak=True)
            await self._state.set_state(AssistantState.LISTENING)
