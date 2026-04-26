from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass

import numpy as np

from jarvis_backend.config import AudioConfig, VadConfig


@dataclass(frozen=True)
class SpeechSegment:
    samples: np.ndarray
    sample_rate: int


class SileroVad:
    def __init__(self, config: VadConfig, audio: AudioConfig) -> None:
        self._config = config
        self._audio = audio
        self._model: object | None = None

    async def load(self) -> None:
        if self._config.engine != "silero":
            return
        try:
            import torch

            self._model, _ = await asyncio.to_thread(
                torch.hub.load,
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                trust_repo=True,
            )
        except Exception:
            self._model = None

    async def is_speech(self, frame: np.ndarray) -> bool:
        rms = float(np.sqrt(np.mean(np.square(frame.astype(np.float32)))))
        if self._model is None:
            return rms > 0.015
        import torch

        tensor = torch.from_numpy(frame.astype(np.float32))
        probability = await asyncio.to_thread(self._model, tensor, self._audio.sample_rate)
        return float(probability.item()) >= self._config.threshold


class UtteranceDetector:
    def __init__(self, vad: SileroVad, audio: AudioConfig) -> None:
        self._vad = vad
        self._audio = audio
        self._frame_samples = int(audio.sample_rate * audio.frame_ms / 1000)
        self._silence_frames = max(1, audio.silence_timeout_ms // audio.frame_ms)
        self._pre_frames = max(1, audio.pre_speech_ms // audio.frame_ms)
        self._pre_buffer: deque[np.ndarray] = deque(maxlen=self._pre_frames)
        self._speech_frames: list[np.ndarray] = []
        self._silence_count = 0

    async def push_frame(self, frame: np.ndarray) -> SpeechSegment | None:
        speech = await self._vad.is_speech(frame)
        if speech:
            if not self._speech_frames:
                self._speech_frames.extend(self._pre_buffer)
            self._speech_frames.append(frame.copy())
            self._silence_count = 0
            return None

        self._pre_buffer.append(frame.copy())
        if not self._speech_frames:
            return None

        self._silence_count += 1
        if self._silence_count < self._silence_frames:
            self._speech_frames.append(frame.copy())
            return None

        samples = np.concatenate(self._speech_frames).astype(np.float32)
        self._speech_frames.clear()
        self._silence_count = 0
        return SpeechSegment(samples=samples, sample_rate=self._audio.sample_rate)
