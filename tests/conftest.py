from pathlib import Path

import pytest

from database.db import initialize_database


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    path = tmp_path / "astra.sqlite3"
    initialize_database(path)
    return path
