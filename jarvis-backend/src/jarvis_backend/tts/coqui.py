from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from jarvis_backend.tts.base import TextToSpeech


class CoquiTts(TextToSpeech):
    def __init__(self, model_name: str = "tts_models/en/ljspeech/vits") -> None:
        self._model_name = model_name
        self._engine: object | None = None

    async def _load(self) -> object:
        if self._engine is None:
            from TTS.api import TTS

            self._engine = await asyncio.to_thread(TTS, self._model_name)
        return self._engine

    async def synthesize(self, text: str) -> Path:
        engine = await self._load()
        output = Path(tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name)
        await asyncio.to_thread(engine.tts_to_file, text=text, file_path=str(output))
        return output
