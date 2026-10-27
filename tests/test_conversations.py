import pytest

from services.conversation_service import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    rename_conversation,
)


def test_create_save_load_rename_and_delete_conversation(database_path):
    first = create_conversation(database_path)
    second = create_conversation(database_path, "Other chat")
    add_message(database_path, first, "user", "Explain orbital mechanics")
    add_message(database_path, first, "assistant", "Think of an orbit as a continuous fall.")

    loaded = get_conversation(database_path, first)
    assert loaded["title"] == "Explain orbital mechanics"
    assert [message["role"] for message in loaded["messages"]] == ["user", "assistant"]
    assert get_conversation(database_path, second)["messages"] == []

    rename_conversation(database_path, first, "Space notes")
    assert get_conversation(database_path, first)["title"] == "Space notes"
    delete_conversation(database_path, first)
    assert get_conversation(database_path, first) is None
    assert [conversation["id"] for conversation in list_conversations(database_path)] == [second]


def test_rejects_invalid_roles_and_missing_conversation(database_path):
    with pytest.raises(ValueError):
        add_message(database_path, "missing", "user", "hello")
    conversation = create_conversation(database_path)
    with pytest.raises(ValueError):
        add_message(database_path, conversation, "system", "hello")
