from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.env import env
from app.main import app


def test_probes_before_startup(client: TestClient) -> None:
    assert client.get('/live').status_code == 200
    response = client.get('/ready')
    assert response.status_code == 503
    assert response.json() == {'status': 'unavailable'}


def test_probes_during_and_after_lifespan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(env, 'DATABASE_URL', f'sqlite:///{tmp_path / "probes.db"}')

    with TestClient(app) as client:
        assert client.get('/live').json() == {'status': 'ok'}
        assert client.get('/ready').json() == {'status': 'ok'}

    assert client.get('/live').status_code == 200
    assert client.get('/ready').status_code == 503


def test_probes_absent_from_openapi(client: TestClient) -> None:
    paths = client.get('/openapi.json').json()['paths']

    assert '/live' not in paths
    assert '/ready' not in paths
