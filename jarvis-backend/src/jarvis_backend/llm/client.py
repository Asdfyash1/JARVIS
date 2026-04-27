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
        if self._config.provider == "gemini":
            async for content in self._gemini(history, user_input):
                yield content
            return
        api_key_env = self._config.openai_api_key_env if self._config.provider == "openai" else self._config.api_key_env
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise RuntimeError(f"{api_key_env} is required")
        messages = [{"role": "system", "content": self._config.system_prompt}]
        messages.extend(
            {"role": self._map_role(message.role), "content": message.content} for message in history
        )
        messages.append({"role": "user", "content": user_input})
        payload = {
            "model": self._config.openai_model if self._config.provider == "openai" else self._config.model,
            "messages": messages,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
            "stream": self._config.streaming,
        }
        base_url = self._config.openai_base_url if self._config.provider == "openai" else self._config.base_url
        url = f"{base_url.rstrip('/')}/chat/completions"
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
                if not self._config.streaming:
                    data = await response.json()
                    content = data["choices"][0]["message"].get("content", "")
                    if content:
                        yield content
                    return
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

    async def _gemini(self, history: list[ChatMessage], user_input: str) -> AsyncIterator[str]:
        api_key = os.environ.get(self._config.gemini_api_key_env)
        if not api_key:
            raise RuntimeError(f"{self._config.gemini_api_key_env} is required")
        contents = [
            {
                "role": "user" if message.role == ChatRole.USER else "model",
                "parts": [{"text": message.content}],
            }
            for message in history
            if message.role in (ChatRole.USER, ChatRole.ASSISTANT)
        ]
        contents.append({"role": "user", "parts": [{"text": user_input}]})
        payload = {
            "systemInstruction": {"parts": [{"text": self._config.system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": self._config.temperature,
                "maxOutputTokens": self._config.max_tokens,
            },
        }
        url = (
            f"{self._config.gemini_base_url.rstrip('/')}/models/"
            f"{self._config.gemini_model}:generateContent?key={api_key}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                content = "".join(str(part.get("text", "")) for part in parts)
                if content:
                    yield content

    @staticmethod
    def _map_role(role: ChatRole) -> str:
        if role == ChatRole.TOOL:
            return "assistant"
        return role.value
