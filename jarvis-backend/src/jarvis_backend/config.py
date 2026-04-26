from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8765
    cors_origins: list[str] = Field(default_factory=list)


class AudioConfig(BaseModel):
    sample_rate: int = 16_000
    channels: int = 1
    frame_ms: int = 30
    silence_timeout_ms: int = 1000
    pre_speech_ms: int = 300
    input_device: int | str | None = None
    output_device: int | str | None = None


class VadConfig(BaseModel):
    engine: Literal["silero", "webrtc"] = "silero"
    threshold: float = 0.55
    min_speech_ms: int = 180


class SttConfig(BaseModel):
    engine: Literal["faster_whisper"] = "faster_whisper"
    model_size: str = "small.en"
    device: str = "auto"
    compute_type: str = "auto"
    beam_size: int = 1
    language: str = "en"


class TtsConfig(BaseModel):
    engine: Literal["piper", "coqui"] = "piper"
    piper_binary: str = "piper"
    voice_model: str = "./voices/en_US-lessac-medium.onnx"
    speaker_id: int | None = None


class LlmConfig(BaseModel):
    base_url: str = "https://integrate.api.nvidia.com/v1"
    model: str = "meta/llama-3.1-70b-instruct"
    api_key_env: str = "NVIDIA_API_KEY"
    temperature: float = 0.3
    max_tokens: int = 1024
    streaming: bool = False
    system_prompt: str


class MemoryConfig(BaseModel):
    sqlite_path: str = "./data/jarvis.sqlite3"
    max_history_messages: int = 24


class ActionsConfig(BaseModel):
    require_confirmation: bool = True
    linux_app_allowlist: dict[str, str] = Field(default_factory=dict)
    browser_debugger_address: str = "127.0.0.1:9222"
    command_allowlist: list[str] = Field(default_factory=list)


class Settings(BaseModel):
    server: ServerConfig
    audio: AudioConfig
    vad: VadConfig
    stt: SttConfig
    tts: TtsConfig
    llm: LlmConfig
    memory: MemoryConfig
    actions: ActionsConfig


def load_settings(path: str | Path = "config.yaml") -> Settings:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return Settings.model_validate(data)
