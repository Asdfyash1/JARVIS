from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TextToSpeech(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> Path:
        raise NotImplementedError
