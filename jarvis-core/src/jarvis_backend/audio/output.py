from __future__ import annotations

import asyncio
from pathlib import Path

from jarvis_backend.config import AudioConfig


class AudioPlayer:
    def __init__(self, config: AudioConfig) -> None:
        self._config = config
        self._process: asyncio.subprocess.Process | None = None

    async def play_wav(self, path: Path) -> None:
        await self.stop()
        self._process = await asyncio.create_subprocess_exec(
            "aplay",
            str(path),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await self._process.wait()
        self._process = None

    async def stop(self) -> None:
        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=1)
            except asyncio.TimeoutError:
                self._process.kill()
