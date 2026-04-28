from __future__ import annotations

from abc import ABC, abstractmethod

from jarvis_backend.audio.vad import SpeechSegment


class SpeechToText(ABC):
    @abstractmethod
    async def transcribe(self, segment: SpeechSegment) -> str:
        raise NotImplementedError
