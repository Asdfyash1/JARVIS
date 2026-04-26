from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from jarvis_backend.state.models import ActionDecision, AgentAction

JSON_BLOCK_RE = re.compile(r"```json\s*(?P<body>.*?)```", re.DOTALL | re.IGNORECASE)


class ActionParser:
    def parse(self, text: str) -> ActionDecision:
        document = self._extract_json(text)
        if document is None:
            return ActionDecision(spoken_response=text.strip(), actions=[])
        spoken_response = str(document.get("spoken_response") or document.get("response") or "").strip()
        if not spoken_response:
            spoken_response = re.sub(JSON_BLOCK_RE, "", text).strip()
        actions = self._parse_actions(document.get("actions") or document.get("action"))
        return ActionDecision(spoken_response=spoken_response, actions=actions)

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        candidates = [match.group("body") for match in JSON_BLOCK_RE.finditer(text)]
        stripped = text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            candidates.append(stripped)
        for candidate in candidates:
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                return data
        return None

    def _parse_actions(self, payload: Any) -> list[AgentAction]:
        if payload is None:
            return []
        items = payload if isinstance(payload, list) else [payload]
        actions: list[AgentAction] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                actions.append(AgentAction.model_validate(item))
            except ValidationError:
                continue
        return actions
