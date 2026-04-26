from __future__ import annotations

from jarvis_backend.config import LlmConfig, TtsConfig
from jarvis_backend.tts.base import TextToSpeech
from jarvis_backend.tts.piper import PiperTts


def build_tts(config: TtsConfig, llm_config: LlmConfig) -> TextToSpeech:
    if config.engine == "coqui":
        from jarvis_backend.tts.coqui import CoquiTts

        return CoquiTts()
    return PiperTts(config)
