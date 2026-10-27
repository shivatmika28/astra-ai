from config import DEFAULT_MODEL, load_config


def test_config_uses_safe_defaults_and_environment(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("ASTRA_DB_PATH", str(tmp_path / "local.sqlite3"))
    config = load_config()
    assert config.api_key is None
    assert config.model == DEFAULT_MODEL
    assert config.database_path == tmp_path / "local.sqlite3"


def test_config_reads_valid_environment(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    config = load_config()
    assert config.api_key == "test-key"
    assert config.model == "gemini-test-model"
