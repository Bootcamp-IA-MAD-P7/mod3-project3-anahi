import pytest

from src.config import get_settings


def test_missing_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        get_settings(env_file=None)


def test_loads_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    settings = get_settings(env_file=None)

    assert settings.groq_api_key == "test-key"
