"""Conversation and message persistence operations."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from database.db import connect


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_conversation(database_path: str | Path, title: str = "New conversation") -> str:
    conversation_id = str(uuid.uuid4())
    now = _now()
    with connect(database_path) as db:
        db.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conversation_id, title.strip() or "New conversation", now, now),
        )
    return conversation_id


def list_conversations(database_path: str | Path) -> list[dict]:
    with connect(database_path) as db:
        rows = db.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_conversation(database_path: str | Path, conversation_id: str) -> dict | None:
    with connect(database_path) as db:
        row = db.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if row is None:
            return None
        messages = db.execute(
            "SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
    return {**dict(row), "messages": [dict(message) for message in messages]}


def add_message(database_path: str | Path, conversation_id: str, role: str, content: str) -> int:
    if role not in {"user", "assistant"}:
        raise ValueError("role must be 'user' or 'assistant'")
    now = _now()
    with connect(database_path) as db:
        exists = db.execute("SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
        if exists is None:
            raise ValueError("conversation does not exist")
        cursor = db.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, now),
        )
        db.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
        if role == "user":
            current = db.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
            if current and current["title"] == "New conversation":
                title = " ".join(content.split())[:60] or "New conversation"
                db.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id))
        return int(cursor.lastrowid)


def rename_conversation(database_path: str | Path, conversation_id: str, title: str) -> None:
    clean_title = " ".join(title.split())[:100]
    if not clean_title:
        raise ValueError("conversation title cannot be blank")
    with connect(database_path) as db:
        cursor = db.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (clean_title, _now(), conversation_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("conversation does not exist")


def delete_conversation(database_path: str | Path, conversation_id: str) -> None:
    with connect(database_path) as db:
        db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))


def clear_conversations(database_path: str | Path) -> None:
    with connect(database_path) as db:
        db.execute("DELETE FROM conversations")
