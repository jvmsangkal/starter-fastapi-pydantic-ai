import json
import logging
import logging.config
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from loguru import logger
from uvicorn.config import LOGGING_CONFIG

from app.env import env
from app.logging import setup_logging


@pytest.fixture
def lines() -> Iterator[list[str]]:
    # Start from uvicorn's own config, which sets propagate=False on its loggers.
    logging.config.dictConfig(LOGGING_CONFIG)
    setup_logging()
    output: list[str] = []
    logger.add(output.append, format='{level} {function}: {message}')
    yield output
    logger.remove()
    logging.root.handlers.clear()


@pytest.fixture
def json_logs(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> Iterator[pytest.CaptureFixture[str]]:
    monkeypatch.setattr(env, 'LOG_JSON', True)
    setup_logging()
    capsys.readouterr()
    yield capsys
    logger.remove()
    logging.root.handlers.clear()


def test_stdlib_logs_go_through_loguru(lines: list[str]) -> None:
    logging.getLogger('uvicorn.error').info('Application startup complete.')
    logging.getLogger('sqlalchemy').warning('pool exhausted')

    assert lines == [
        'INFO test_stdlib_logs_go_through_loguru: Application startup complete.\n',
        'WARNING test_stdlib_logs_go_through_loguru: pool exhausted\n',
    ]


def test_json_lines(json_logs: pytest.CaptureFixture[str]) -> None:
    logger.info('hello')
    try:
        raise ZeroDivisionError('division by zero')
    except ZeroDivisionError:
        logging.getLogger('sqlalchemy').exception('query failed')

    first, second = map(json.loads, json_logs.readouterr().err.splitlines())
    assert first.keys() == {'time', 'level', 'message', 'location', 'request_id'}
    assert first['level'] == 'INFO'
    assert first['message'] == 'hello'
    assert first['request_id'] == '-'
    assert first['location'].startswith(f'{__name__}:test_json_lines:')
    assert second['message'] == 'query failed'
    assert second['location'].startswith(f'{__name__}:test_json_lines:')
    assert 'ZeroDivisionError: division by zero' in second['exception']


def test_json_access_line_has_request_id(
    json_logs: pytest.CaptureFixture[str], client: TestClient
) -> None:
    client.get(
        '/health',
        headers={'x-request-id': 'abc-123', 'authorization': 'Bearer secret'},
    )

    output = json_logs.readouterr().err
    access = [
        line
        for line in map(json.loads, output.splitlines())
        if line['message'].startswith('GET /health 200')
    ]
    assert len(access) == 1
    assert access[0]['request_id'] == 'abc-123'
    assert 'secret' not in output
