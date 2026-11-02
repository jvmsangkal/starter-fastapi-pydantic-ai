import json
import logging
import logging.config
from collections.abc import Iterator

import pytest
from loguru import logger
from uvicorn.config import LOGGING_CONFIG

from app.env import env
from app.logging import redact_headers, setup_logging


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
    logging.getLogger('uvicorn.access').info('%s - "GET /health"', '127.0.0.1')
    logging.getLogger('sqlalchemy').warning('pool exhausted')

    assert lines == [
        'INFO test_stdlib_logs_go_through_loguru: 127.0.0.1 - "GET /health"\n',
        'WARNING test_stdlib_logs_go_through_loguru: pool exhausted\n',
    ]


def test_json_lines(json_logs: pytest.CaptureFixture[str]) -> None:
    logger.info('hello')
    try:
        raise ZeroDivisionError('division by zero')
    except ZeroDivisionError:
        logging.getLogger('sqlalchemy').exception('query failed')

    first, second = map(json.loads, json_logs.readouterr().err.splitlines())
    assert first.keys() == {'time', 'level', 'message', 'location'}
    assert first['level'] == 'INFO'
    assert first['message'] == 'hello'
    assert first['location'].startswith(f'{__name__}:test_json_lines:')
    assert second['message'] == 'query failed'
    assert second['location'].startswith(f'{__name__}:test_json_lines:')
    assert 'ZeroDivisionError: division by zero' in second['exception']


def test_redact_headers() -> None:
    headers = {
        'Authorization': 'Bearer secret',
        'cookie': 'session=secret',
        'Set-Cookie': 'session=secret',
        'X-API-Key': 'secret',
        'accept': 'application/json',
    }

    assert redact_headers(headers) == {
        'Authorization': '[REDACTED]',
        'cookie': '[REDACTED]',
        'Set-Cookie': '[REDACTED]',
        'X-API-Key': '[REDACTED]',
        'accept': 'application/json',
    }
