from __future__ import annotations

from jarvis_backend.config import SttConfig
from jarvis_backend.stt.base import SpeechToText
from jarvis_backend.stt.faster_whisper import FasterWhisperStt


def build_stt(config: SttConfig) -> SpeechToText:
    return FasterWhisperStt(config)
