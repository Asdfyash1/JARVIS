from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from jarvis_backend.state.models import ActionDecision, AgentAction

JSON_BLOCK_RE = re.compile(r"```json\s*(?P<body>.*?)```", re.DOTALL | re.IGNORECASE)
RAW_ACTIONS_RE = re.compile(r"\bactions?\s*:\s*(?:\[[\s\S]*\]|\{[\s\S]*\})\s*$", re.IGNORECASE)


class ActionParser:
    def parse(self, text: str) -> ActionDecision:
        document = self._extract_json(text)
        if document is None:
            return ActionDecision(spoken_response=self._clean_spoken_response(text), actions=[])
        if "choices" in document:
            content = (
                document.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return self.parse(str(content))
        if "action" in document and "spoken_response" not in document and "response" not in document:
            actions = self._parse_actions(document)
            action_name = actions[0].action.replace("_", " ") if actions else "that action"
            return ActionDecision(spoken_response=f"I can do {action_name}. Please confirm first.", actions=actions)
        spoken_response = self._clean_spoken_response(
            str(document.get("spoken_response") or document.get("response") or "")
        )
        if not spoken_response:
            spoken_response = self._clean_spoken_response(re.sub(JSON_BLOCK_RE, "", text))
        actions = self._parse_actions(document.get("actions") or document.get("action"))
        return ActionDecision(spoken_response=spoken_response, actions=actions)

    @staticmethod
    def _clean_spoken_response(text: str) -> str:
        return re.sub(RAW_ACTIONS_RE, "", text).strip()

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
