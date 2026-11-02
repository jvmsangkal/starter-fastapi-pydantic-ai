from pathlib import Path

import pytest

from app.env import Settings, load_env


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Run from an empty directory with the app's vars unset, so neither the real
    # environment nor a developer's .env leaks into these tests.
    monkeypatch.chdir(tmp_path)
    for name in Settings.model_fields:
        monkeypatch.delenv(name, raising=False)


def test_defaults_load_without_any_env() -> None:
    env = load_env()

    assert env.DATABASE_URL == 'sqlite:///./app.db'
    assert env.OPENAI_API_KEY is None
    assert env.LOG_LEVEL == 'INFO'


def test_reads_dotenv_file(tmp_path: Path) -> None:
    (tmp_path / '.env').write_text('OPENAI_API_KEY=sk-test\nUNRELATED=ignored\n')

    key = load_env().OPENAI_API_KEY

    assert key is not None
    assert key.get_secret_value() == 'sk-test'


def test_invalid_env_lists_every_bad_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('DATABASE_URL', 'user:hunter2@localhost/db')
    monkeypatch.setenv('OPENAI_API_KEY', '')

    with pytest.raises(SystemExit) as exc_info:
        load_env()

    message = str(exc_info.value)
    assert message.startswith('Invalid environment variables:')
    assert 'DATABASE_URL: Value error, not a valid SQLAlchemy database URL' in message
    assert 'OPENAI_API_KEY: Value error, must not be empty' in message
    assert 'hunter2' not in message
