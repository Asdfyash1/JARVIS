from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jarvis_backend.actions.manager import ActionManager
from jarvis_backend.agent import JarvisAgent
from jarvis_backend.audio.input import MicrophoneStream
from jarvis_backend.audio.output import AudioPlayer
from jarvis_backend.audio.pipeline import VoicePipeline
from jarvis_backend.audio.vad import SileroVad, SpeechSegment, UtteranceDetector
from jarvis_backend.config import Settings
from jarvis_backend.events import Event, EventBus
from jarvis_backend.llm.action_parser import ActionParser
from jarvis_backend.llm.client import NvidiaLlmClient
from jarvis_backend.memory.store import ConversationMemory
from jarvis_backend.state.store import StateStore
from jarvis_backend.stt.factory import build_stt
from jarvis_backend.tts.factory import build_tts


class TextInput(BaseModel):
    text: str
    speak: bool = True


class ConfirmationInput(BaseModel):
    action_id: str
    approved: bool


class Runtime:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.event_bus = EventBus()
        self.state = StateStore(self.event_bus)
        self.memory = ConversationMemory(
            settings.memory.sqlite_path,
            settings.memory.max_history_messages,
        )
        self.vad = SileroVad(settings.vad, settings.audio)
        self.stt = build_stt(settings.stt)
        self.tts = build_tts(settings.tts, settings.llm)
        self.player = AudioPlayer(settings.audio)
        self.llm = NvidiaLlmClient(settings.llm)
        self.actions = ActionManager(settings.actions, self.event_bus, self.state)
        self.agent = JarvisAgent(
            self.event_bus,
            self.state,
            self.memory,
            self.llm,
            ActionParser(),
            self.tts,
            self.player,
            self.actions,
        )
        self.voice = VoicePipeline(
            MicrophoneStream(settings.audio),
            UtteranceDetector(self.vad, settings.audio),
            self.stt,
            self.agent,
            self.event_bus,
            self.state,
        )

    async def initialize(self) -> None:
        await self.memory.initialize()
        await self.vad.load()


def build_app(settings: Settings) -> FastAPI:
    runtime = Runtime(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await runtime.initialize()
        yield
        await runtime.voice.stop()

    app = FastAPI(title="Project Jarvis Backend", version="0.1.0", lifespan=lifespan)
    app.state.runtime = runtime
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "state": runtime.state.state.value}

    @app.post("/api/input")
    async def input_text(payload: TextInput) -> dict[str, str]:
        reply = await runtime.agent.handle_user_text_wait(payload.text, speak=payload.speak)
        return {"status": "ok", "reply": reply}

    @app.post("/api/voice/start")
    async def voice_start() -> dict[str, str]:
        await runtime.voice.start()
        return {"status": "listening"}

    @app.post("/api/voice/stop")
    async def voice_stop() -> dict[str, str]:
        await runtime.voice.stop()
        return {"status": "stopped"}

    @app.post("/api/voice/transcribe")
    async def voice_transcribe(file: UploadFile = File(...)) -> dict[str, str]:
        import io

        import soundfile as sf

        body = await file.read()
        samples, sample_rate = sf.read(io.BytesIO(body), dtype="float32")
        if len(samples.shape) > 1:
            samples = samples.mean(axis=1)
        segment = SpeechSegment(samples=samples, sample_rate=int(sample_rate))
        text = await runtime.stt.transcribe(segment)
        await runtime.event_bus.publish("transcription", {"text": text})
        reply = ""
        if text:
            reply = await runtime.agent.handle_user_text_wait(text, speak=False, emit=False)
            await runtime.event_bus.publish("ai_response", {"text": reply, "actions": []})
        return {"status": "ok", "text": text, "reply": reply}

    @app.post("/api/interrupt")
    async def interrupt() -> dict[str, str]:
        await runtime.agent.interrupt()
        return {"status": "interrupted"}

    @app.post("/api/action/confirm")
    async def confirm(payload: ConfirmationInput) -> dict[str, str]:
        await runtime.actions.approve(payload.action_id, payload.approved)
        return {"status": "accepted"}

    @app.websocket("/ws")
    async def websocket(websocket: WebSocket) -> None:
        await websocket.accept()
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=256)
        runtime.event_bus.subscribe(queue)
        try:
            await websocket.send_json({"type": "system_state", "payload": {"state": runtime.state.state.value}})
            while True:
                event = await queue.get()
                await websocket.send_json(event.model_dump(mode="json"))
        except WebSocketDisconnect:
            pass
        finally:
            runtime.event_bus.unsubscribe(queue)

    return app
