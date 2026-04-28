from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import soundfile as sf

from jarvis_backend.config import TtsConfig
from jarvis_backend.tts.base import TextToSpeech


DEFAULT_VOICE_PROFILES = {
    "female_thick": (
        "A confident adult woman with a deeper, thicker, warm contralto voice, "
        "calm Jarvis assistant tone, clear articulation, cinematic presence"
    ),
    "male_thick": (
        "A confident adult man with a deep, thick, warm baritone voice, "
        "calm Jarvis assistant tone, clear articulation, cinematic presence"
    ),
}


class VoxCpmTts(TextToSpeech):
    def __init__(self, config: TtsConfig) -> None:
        self._config = config
        self._model: object | None = None

    async def _load(self) -> object:
        if self._model is not None:
            return self._model

        def load_model() -> object:
            from voxcpm import VoxCPM

            model_path = self._config.voxcpm_local_dir or self._config.voxcpm_model
            return VoxCPM.from_pretrained(
                model_path,
                load_denoiser=self._config.voxcpm_load_denoiser,
            )

        self._model = await asyncio.to_thread(load_model)
        return self._model

    async def synthesize(self, text: str) -> Path:
        model = await self._load()
        output = Path(tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name)
        voice_prompt = self._voice_prompt()
        designed_text = f"({voice_prompt}){text}" if voice_prompt else text

        def generate() -> None:
            wav = model.generate(
                text=designed_text,
                cfg_value=self._config.voxcpm_cfg_value,
                inference_timesteps=self._config.voxcpm_inference_timesteps,
            )
            sample_rate = int(model.tts_model.sample_rate)
            sf.write(output, wav, sample_rate)

        await asyncio.to_thread(generate)
        return output

    def _voice_prompt(self) -> str:
        profiles = {**DEFAULT_VOICE_PROFILES, **self._config.voice_profiles}
        return profiles.get(self._config.voice_profile, profiles["female_thick"])
