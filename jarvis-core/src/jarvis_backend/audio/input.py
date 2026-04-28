from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import numpy as np

from jarvis_backend.config import AudioConfig


class MicrophoneStream:
    def __init__(self, config: AudioConfig) -> None:
        self._config = config
        self._frame_samples = int(config.sample_rate * config.frame_ms / 1000)

    async def frames(self) -> AsyncIterator[np.ndarray]:
        import sounddevice as sd

        queue: asyncio.Queue[np.ndarray] = asyncio.Queue(maxsize=64)
        loop = asyncio.get_running_loop()

        def callback(indata: np.ndarray, _frames: int, _time: object, status: object) -> None:
            if status:
                return
            frame = np.asarray(indata[:, 0], dtype=np.float32).copy()
            loop.call_soon_threadsafe(queue.put_nowait, frame)

        with sd.InputStream(
            samplerate=self._config.sample_rate,
            channels=self._config.channels,
            blocksize=self._frame_samples,
            device=self._config.input_device,
            dtype="float32",
            callback=callback,
        ):
            while True:
                yield await queue.get()
