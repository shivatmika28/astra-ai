"""Gemini API integration through Google's official google-genai SDK."""

from __future__ import annotations

from dataclasses import dataclass

from config import MAX_CONTEXT_MESSAGES
from system_prompt import build_system_instruction


class GeminiServiceError(RuntimeError):
    """An actionable error returned by the Gemini service layer."""


@dataclass(frozen=True)
class ReplyPreferences:
    mode: str = "Companion"
    level: str = "Standard"
    style: str = "Warm and clear"
    response_length: str = "Balanced"
    model: str | None = None


def build_history(messages: list[dict], limit: int = MAX_CONTEXT_MESSAGES) -> list[dict[str, object]]:
    """Convert stored chat messages into the role/parts format expected by Gemini."""
    recent = [message for message in messages if message.get("role") in {"user", "assistant", "model"}]
    recent = recent[-limit:]
    history: list[dict[str, object]] = []
    for message in recent:
        text = str(message.get("content", "")).strip()
        if not text:
            continue
        role = "model" if message["role"] in {"assistant", "model"} else "user"
        history.append({"role": role, "parts": [{"text": text}]})
    return history


def _error_message(error: Exception) -> str | None:
    status = getattr(error, "status_code", None) or getattr(error, "code", None)
    module_name = type(error).__module__
    error_name = type(error).__name__.lower()
    detail = str(error).lower()
    if status in (401, 403) or "unauthenticated" in detail or "permission_denied" in detail or "api key" in detail:
        return "Gemini rejected the API key. Check GEMINI_API_KEY in your .env file or Streamlit secrets."
    if status == 404 or "not found" in detail or "model" in detail and "unsupported" in detail:
        return "The selected Gemini model is unavailable. Choose a supported model or update GEMINI_MODEL."
    if status == 429 or "resource_exhausted" in detail or "rate limit" in detail:
        return "Gemini rate limit reached. Wait a little, then try again."
    if isinstance(error, (TimeoutError, ConnectionError)) or "timeout" in error_name or "network" in error_name or module_name.startswith("httpx"):
        return "Could not reach Gemini because of a network timeout. Check your connection and try again."
    if status or module_name.startswith(("google.genai", "httpx")):
        return "Gemini could not complete the request. Check the model and API configuration, then try again."
    return None


def generate_reply(
    *,
    api_key: str | None,
    model: str,
    messages: list[dict],
    preferences: ReplyPreferences | None = None,
    memories: list[str] | None = None,
    document: str | None = None,
    client=None,
) -> str:
    """Generate a real answer; never substitute a canned response for API failure."""
    if not api_key and client is None:
        raise GeminiServiceError("Gemini is not configured. Add GEMINI_API_KEY to .env or Streamlit secrets.")
    history = build_history(messages)
    if not history or history[-1]["role"] != "user":
        raise GeminiServiceError("Enter a message before asking Astra to respond.")
    preferences = preferences or ReplyPreferences()
    if client is None:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)
        except (ImportError, ValueError) as exc:
            raise GeminiServiceError("The Gemini SDK could not be initialized. Reinstall requirements.txt and check your API key.") from exc

    system_instruction = build_system_instruction(
        mode=preferences.mode,
        level=preferences.level,
        style=preferences.style,
        response_length=preferences.response_length,
        memories=memories or [],
        document=document,
    )
    output_limits = {"Concise": 700, "Balanced": 1400, "Detailed": 2500}
    request_config = {
        "system_instruction": system_instruction,
        "max_output_tokens": output_limits.get(preferences.response_length, 1400),
        "temperature": 0.7,
    }
    try:
        response = client.models.generate_content(
            model=preferences.model or model,
            contents=history,
            config=request_config,
        )
    except Exception as exc:
        message = _error_message(exc)
        if message:
            raise GeminiServiceError(message) from None
        raise
    answer = getattr(response, "text", None)
    if not isinstance(answer, str) or not answer.strip():
        raise GeminiServiceError("Gemini returned an empty response. Your conversation is saved; try again.")
    return answer.strip()
