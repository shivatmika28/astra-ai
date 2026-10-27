"""Application configuration loaded from environment variables and .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = "gemini-3.8-flash"
MODEL_OPTIONS = (
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
)
MAX_CONTEXT_MESSAGES = 20
MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_DOCUMENT_CHARS = 24_000


@dataclass(frozen=True)
class AppConfig:
    api_key: str | None
    model: str
    database_path: Path


def _streamlit_secret(name: str) -> str | None:
    """Read a Streamlit Cloud secret when available, without requiring Streamlit."""
    try:
        import streamlit as st

        value = st.secrets.get(name)
    except (ImportError, FileNotFoundError, RuntimeError, AttributeError):
        return None
    return str(value) if value else None


def load_config() -> AppConfig:
    """Load local .env values, then environment or Streamlit secrets."""
    load_dotenv(BASE_DIR / ".env")
    api_key = os.getenv("GEMINI_API_KEY") or _streamlit_secret("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL") or _streamlit_secret("GEMINI_MODEL") or DEFAULT_MODEL
    database = os.getenv("ASTRA_DB_PATH") or str(BASE_DIR / "data" / "astra.sqlite3")
    return AppConfig(api_key=api_key, model=model.strip(), database_path=Path(database).expanduser())
