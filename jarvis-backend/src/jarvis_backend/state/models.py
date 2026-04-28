from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


class AssistantState(StrEnum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    SPEAKING = "speaking"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    EXECUTING_ACTION = "executing_action"
    ERROR = "error"


class ChatRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: ChatRole
    content: str


class AgentAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: Literal[
        "open_app",
        "close_app",
        "focus_window",
        "open_website",
        "google_search",
        "youtube_control",
        "whatsapp_message",
        "system_command",
    ]
    app_name: str | None = None
    window_title: str | None = None
    url: HttpUrl | None = None
    query: str | None = None
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    contact: str | None = None
    phone_number: str | None = None
    message: str | None = None
    youtube_command: Literal["play", "pause", "next", "previous", "search"] | None = None
    requires_confirmation: bool = True


class ActionDecision(BaseModel):
    spoken_response: str
    actions: list[AgentAction] = Field(default_factory=list)


class ConfirmationRequest(BaseModel):
    action: AgentAction
    prompt: str
