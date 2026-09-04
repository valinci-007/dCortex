"""Persistent conversations (ChatGPT-style history) for the desk.

One SQLite file (separate from the read-only dataset database) holds chats and
their messages. There is no user model — the brief puts authentication out of
scope — so this is the history of one desk. Each chat remembers the model
session it belongs to (`session_id`) so a conversation can be resumed after a
server restart, plus the full answer objects so the reasoning trail and trace
are still there when a chat is reopened.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS chats (
    id         TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    provider   TEXT NOT NULL,
    session_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id     TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    answer_json TEXT,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, id);
"""

TITLE_MAX = 60


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def title_from(question: str) -> str:
    """A ChatGPT-style title: the first line of the first question, trimmed."""
    line = " ".join(question.strip().split())
    if len(line) <= TITLE_MAX:
        return line or "New chat"
    cut = line[: TITLE_MAX - 1]
    if " " in cut[20:]:
        cut = cut[: cut.rfind(" ")]
    return cut + "…"


@dataclass(frozen=True, slots=True)
class ChatRecord:
    id: str
    title: str
    provider: str
    session_id: str | None
    created_at: str
    updated_at: str
    message_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "provider": self.provider,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
        }


@dataclass(frozen=True, slots=True)
class MessageRecord:
    id: int
    chat_id: str
    role: str
    content: str
    created_at: str
    answer: dict[str, Any] | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
            "answer": self.answer,
        }


class ChatStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    # ---- chats -----------------------------------------------------------

    def create(self, *, provider: str, title: str | None = None) -> ChatRecord:
        now = _now()
        chat_id = uuid.uuid4().hex
        with self._conn:
            self._conn.execute(
                "INSERT INTO chats (id, title, provider, session_id, created_at, updated_at) "
                "VALUES (?, ?, ?, NULL, ?, ?)",
                (chat_id, title or "New chat", provider, now, now),
            )
        return self.get(chat_id)  # type: ignore[return-value]

    def get(self, chat_id: str) -> ChatRecord | None:
        row = self._conn.execute(
            "SELECT c.*, (SELECT COUNT(*) FROM messages m WHERE m.chat_id = c.id) AS n "
            "FROM chats c WHERE c.id = ?",
            (chat_id,),
        ).fetchone()
        return self._chat(row) if row else None

    def list(self, *, limit: int = 200) -> list[ChatRecord]:
        rows = self._conn.execute(
            "SELECT c.*, (SELECT COUNT(*) FROM messages m WHERE m.chat_id = c.id) AS n "
            "FROM chats c ORDER BY c.updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._chat(r) for r in rows]

    def rename(self, chat_id: str, title: str) -> ChatRecord | None:
        with self._conn:
            self._conn.execute(
                "UPDATE chats SET title = ?, updated_at = ? WHERE id = ?",
                (title.strip()[:TITLE_MAX] or "New chat", _now(), chat_id),
            )
        return self.get(chat_id)

    def set_session(self, chat_id: str, session_id: str | None) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE chats SET session_id = ? WHERE id = ?", (session_id, chat_id)
            )

    def delete(self, chat_id: str) -> bool:
        with self._conn:
            cur = self._conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        return cur.rowcount > 0

    # ---- messages ----------------------------------------------------------

    def messages(self, chat_id: str) -> list[MessageRecord]:
        rows = self._conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY id", (chat_id,)
        ).fetchall()
        return [self._message(r) for r in rows]

    def append(
        self, chat_id: str, role: str, content: str, *, answer: dict[str, Any] | None = None
    ) -> MessageRecord:
        now = _now()
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO messages (chat_id, role, content, answer_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (chat_id, role, content, json.dumps(answer, default=str) if answer else None, now),
            )
            self._conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (now, chat_id))
            if role == "user":
                # first question names the chat
                self._conn.execute(
                    "UPDATE chats SET title = ? WHERE id = ? AND title = 'New chat'",
                    (title_from(content), chat_id),
                )
        row = self._conn.execute("SELECT * FROM messages WHERE id = ?", (cur.lastrowid,)).fetchone()
        return self._message(row)

    def exchanges(self, chat_id: str) -> list[tuple[str, str]]:
        """(question, answer text) pairs, in order — for re-seeding a model session."""
        pairs: list[tuple[str, str]] = []
        pending: str | None = None
        for m in self.messages(chat_id):
            if m.role == "user":
                pending = m.content
            elif pending is not None:
                pairs.append((pending, m.content))
                pending = None
        return pairs

    # ---- mapping -----------------------------------------------------------

    @staticmethod
    def _chat(row: sqlite3.Row) -> ChatRecord:
        return ChatRecord(
            id=row["id"],
            title=row["title"],
            provider=row["provider"],
            session_id=row["session_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            message_count=int(row["n"]) if "n" in row.keys() else 0,
        )

    @staticmethod
    def _message(row: sqlite3.Row) -> MessageRecord:
        return MessageRecord(
            id=int(row["id"]),
            chat_id=row["chat_id"],
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"],
            answer=json.loads(row["answer_json"]) if row["answer_json"] else None,
        )
