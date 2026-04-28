from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

from jarvis_backend.state.models import ChatMessage, ChatRole


class ConversationMemory:
    def __init__(self, sqlite_path: str, max_history_messages: int) -> None:
        self._path = Path(sqlite_path)
        self._max_history_messages = max_history_messages
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        async with self._lock:
            with sqlite3.connect(self._path) as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                connection.commit()

    async def append(self, message: ChatMessage) -> None:
        async with self._lock:
            with sqlite3.connect(self._path) as connection:
                connection.execute(
                    "INSERT INTO messages (id, role, content) VALUES (?, ?, ?)",
                    (message.id, message.role.value, message.content),
                )
                connection.commit()

    async def history(self) -> list[ChatMessage]:
        async with self._lock:
            with sqlite3.connect(self._path) as connection:
                rows = connection.execute(
                    """
                    SELECT id, role, content
                    FROM messages
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (self._max_history_messages,),
                ).fetchall()
        messages = [
            ChatMessage(id=row[0], role=ChatRole(row[1]), content=row[2]) for row in reversed(rows)
        ]
        return messages
