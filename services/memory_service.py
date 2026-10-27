"""Explicit, user-managed long-term memory and settings persistence."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from database.db import connect

_CREDENTIAL_TERMS = re.compile(r"\b(api[ _-]?key|password|passcode|secret|token|authorization|private key)\b|AIza[0-9A-Za-z_-]{20,}", re.IGNORECASE)


def _clean_memory(content: str) -> str:
    clean = " ".join(content.split())
    if not clean or len(clean) > 500:
        raise ValueError("memory must contain 1 to 500 characters")
    if _CREDENTIAL_TERMS.search(clean):
        raise ValueError("Do not save passwords, API keys, tokens, or other credentials as memories")
    return clean


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_memories(database_path: str | Path) -> list[dict]:
    with connect(database_path) as db:
        rows = db.execute("SELECT id, content FROM memories ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def add_memory(database_path: str | Path, content: str) -> int:
    clean = _clean_memory(content)
    now = _now()
    with connect(database_path) as db:
        cursor = db.execute("INSERT INTO memories (content, created_at, updated_at) VALUES (?, ?, ?)", (clean, now, now))
        return int(cursor.lastrowid)


def update_memory(database_path: str | Path, memory_id: int, content: str) -> None:
    clean = _clean_memory(content)
    with connect(database_path) as db:
        cursor = db.execute("UPDATE memories SET content = ?, updated_at = ? WHERE id = ?", (clean, _now(), memory_id))
        if not cursor.rowcount:
            raise ValueError("memory does not exist")


def delete_memory(database_path: str | Path, memory_id: int) -> None:
    with connect(database_path) as db:
        db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))


def get_settings(database_path: str | Path) -> dict:
    with connect(database_path) as db:
        rows = db.execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: json.loads(row["value"]) for row in rows}


def save_settings(database_path: str | Path, settings: dict) -> None:
    with connect(database_path) as db:
        db.executemany(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            [(key, json.dumps(value)) for key, value in settings.items()],
        )
