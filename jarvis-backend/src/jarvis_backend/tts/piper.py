from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from jarvis_backend.config import TtsConfig
from jarvis_backend.tts.base import TextToSpeech


class PiperTts(TextToSpeech):
    def __init__(self, config: TtsConfig) -> None:
        self._config = config

    async def synthesize(self, text: str) -> Path:
        output = Path(tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name)
        command = [
            self._config.piper_binary,
            "--model",
            self._config.voice_model,
            "--output_file",
            str(output),
        ]
        if self._config.speaker_id is not None:
            command.extend(["--speaker", str(self._config.speaker_id)])
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, stderr = await process.communicate(text.encode("utf-8"))
        if process.returncode != 0:
            raise RuntimeError(stderr.decode("utf-8", errors="replace"))
        return output
