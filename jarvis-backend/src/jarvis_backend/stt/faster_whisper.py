from __future__ import annotations

import asyncio

from jarvis_backend.audio.vad import SpeechSegment
from jarvis_backend.config import SttConfig
from jarvis_backend.stt.base import SpeechToText


class FasterWhisperStt(SpeechToText):
    def __init__(self, config: SttConfig) -> None:
        self._config = config
        self._model: object | None = None

    async def load(self) -> None:
        from faster_whisper import WhisperModel

        device = "cuda" if self._config.device == "auto" else self._config.device
        compute_type = "float16" if self._config.compute_type == "auto" else self._config.compute_type
        try:
            self._model = await asyncio.to_thread(
                WhisperModel,
                self._config.model_size,
                device=device,
                compute_type=compute_type,
            )
        except Exception:
            self._model = await asyncio.to_thread(
                WhisperModel,
                self._config.model_size,
                device="cpu",
                compute_type="int8",
            )

    async def transcribe(self, segment: SpeechSegment) -> str:
        if self._model is None:
            await self.load()
        assert self._model is not None

        def run_transcription() -> str:
            segments, _info = self._model.transcribe(
                segment.samples,
                beam_size=self._config.beam_size,
                language=self._config.language,
                vad_filter=False,
            )
            return " ".join(item.text.strip() for item in segments).strip()

        return await asyncio.to_thread(run_transcription)
