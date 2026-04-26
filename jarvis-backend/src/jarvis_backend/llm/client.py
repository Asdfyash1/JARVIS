from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

import aiohttp

from jarvis_backend.config import LlmConfig
from jarvis_backend.state.models import ChatMessage, ChatRole


class NvidiaLlmClient:
    def __init__(self, config: LlmConfig) -> None:
        self._config = config

    async def stream(self, history: list[ChatMessage], user_input: str) -> AsyncIterator[str]:
        api_key = os.environ.get(self._config.api_key_env)
        if not api_key:
            raise RuntimeError(f"{self._config.api_key_env} is required")
        messages = [{"role": "system", "content": self._config.system_prompt}]
        messages.extend(
            {"role": self._map_role(message.role), "content": message.content} for message in history
        )
        messages.append({"role": "user", "content": user_input})
        payload = {
            "model": self._config.model,
            "messages": messages,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
            "stream": True,
        }
        url = f"{self._config.base_url.rstrip('/')}/chat/completions"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as response:
                response.raise_for_status()
                async for raw_line in response.content:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content") or delta.get("reasoning_content")
                    if content:
                        yield content

    @staticmethod
    def _map_role(role: ChatRole) -> str:
        if role == ChatRole.TOOL:
            return "assistant"
        return role.value
