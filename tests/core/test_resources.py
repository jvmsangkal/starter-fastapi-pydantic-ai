from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.pool import QueuePool

from app.core.env import env
from app.main import app


def test_lifespan_opens_and_disposes_engine(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_path = tmp_path / 'lifespan.db'
    monkeypatch.setattr(env, 'DATABASE_URL', f'sqlite:///{db_path}')
    command.upgrade(Config(Path(__file__).parents[2] / 'alembic.ini'), 'head')

    with TestClient(app) as client:
        assert app.state.engine.url.database == str(db_path)
        assert client.post('/v1/items', json={'name': 'first'}).status_code == 200
        assert client.get('/v1/items').json() == [{'id': 1, 'name': 'first'}]
        pool = app.state.engine.pool
        assert isinstance(pool, QueuePool)
        assert pool.checkedin() == 1

    assert pool.checkedin() == 0
