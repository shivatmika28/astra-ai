from database.db import connect, initialize_database


def test_database_initialization_is_repeatable(tmp_path):
    path = tmp_path / "nested" / "astra.sqlite3"
    initialize_database(path)
    initialize_database(path)
    with connect(path) as db:
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"conversations", "messages", "memories", "settings"} <= names
