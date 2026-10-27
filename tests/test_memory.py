import pytest

from services.memory_service import add_memory, delete_memory, get_settings, list_memories, save_settings, update_memory


def test_memory_crud_and_settings(database_path):
    memory_id = add_memory(database_path, "  Prefers   Python examples ")
    assert list_memories(database_path) == [{"id": memory_id, "content": "Prefers Python examples"}]
    update_memory(database_path, memory_id, "Learning astronomy")
    assert list_memories(database_path)[0]["content"] == "Learning astronomy"
    delete_memory(database_path, memory_id)
    assert list_memories(database_path) == []

    save_settings(database_path, {"level": "Advanced", "memory_enabled": False})
    save_settings(database_path, {"level": "Beginner"})
    assert get_settings(database_path) == {"level": "Beginner", "memory_enabled": False}


def test_memory_validation(database_path):
    with pytest.raises(ValueError):
        add_memory(database_path, "  ")
    with pytest.raises(ValueError):
        add_memory(database_path, "x" * 501)
