from types import SimpleNamespace

import pytest

from services.gemini_service import GeminiServiceError, ReplyPreferences, build_history, generate_reply
from utils.validation import clean_title, clean_user_message


class FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.kwargs = None

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, response=None, error=None):
        self.models = FakeModels(response, error)


def test_build_history_maps_roles_and_limits_context():
    history = build_history([
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old reply"},
        {"role": "user", "content": "new"},
    ], limit=2)
    assert history == [
        {"role": "model", "parts": [{"text": "old reply"}]},
        {"role": "user", "parts": [{"text": "new"}]},
    ]


def test_generate_reply_uses_mocked_gemini_and_preferences():
    client = FakeClient(response=SimpleNamespace(text="  Hello from Astra.  "))
    reply = generate_reply(
        api_key="test-key", model="gemini-example", messages=[{"role": "user", "content": "Hi"}],
        preferences=ReplyPreferences(mode="Learning", level="Beginner", model="gemini-override"), client=client,
    )
    assert reply == "Hello from Astra."
    assert client.models.kwargs["model"] == "gemini-override"
    assert client.models.kwargs["contents"][-1]["role"] == "user"
    assert "Beginner" in client.models.kwargs["config"]["system_instruction"]


def test_missing_key_and_api_errors_are_actionable():
    with pytest.raises(GeminiServiceError, match="GEMINI_API_KEY"):
        generate_reply(api_key=None, model="m", messages=[{"role": "user", "content": "Hi"}])

    rate_limit = RuntimeError("resource exhausted")
    rate_limit.status_code = 429
    with pytest.raises(GeminiServiceError, match="rate limit"):
        generate_reply(
            api_key="test-key", model="m", messages=[{"role": "user", "content": "Hi"}],
            client=FakeClient(error=rate_limit),
        )


def test_empty_model_response_is_not_fabricated():
    with pytest.raises(GeminiServiceError, match="empty response"):
        generate_reply(
            api_key="test-key", model="m", messages=[{"role": "user", "content": "Hi"}],
            client=FakeClient(response=SimpleNamespace(text="  ")),
        )


def test_input_validation():
    assert clean_user_message("  hello  ") == "hello"
    assert clean_title(" A   title ") == "A title"
    with pytest.raises(ValueError):
        clean_user_message("  ")
    with pytest.raises(ValueError):
        clean_user_message("x" * 20_001)
    with pytest.raises(ValueError):
        clean_title("\n ")
