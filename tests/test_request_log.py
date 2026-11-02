import logging
import logging.config
import re
import uuid
from collections.abc import Iterator

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from loguru import logger
from uvicorn.config import LOGGING_CONFIG

from app.logging import setup_logging
from app.request_log import RequestLogMiddleware, redact_headers

demo = FastAPI()
demo.add_middleware(RequestLogMiddleware)


@demo.get('/work')
def work() -> dict[str, str]:
    # Sync route, so this runs in the threadpool and logs through stdlib logging.
    logging.getLogger('app.work').info('working')
    return {'status': 'ok'}


@demo.get('/live')
def live() -> dict[str, str]:
    return {'status': 'ok'}


@demo.get('/boom')
def boom() -> None:
    raise RuntimeError('boom')


@demo.exception_handler(Exception)
async def handle_exception(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse({'detail': f'handled: {exc}'}, status_code=500)


@pytest.fixture
def lines() -> Iterator[list[str]]:
    logging.config.dictConfig(LOGGING_CONFIG)
    setup_logging()
    output: list[str] = []
    # TestClient's httpx logs each request it sends; leave those out.
    logger.add(
        output.append,
        format='{extra[request_id]} {message}',
        filter={'httpx': False, 'httpx2': False},
    )
    yield output
    logger.remove()
    logging.root.handlers.clear()


def test_echoes_provided_request_id(client: TestClient) -> None:
    response = client.get('/health', headers={'x-request-id': 'abc-123'})

    assert response.headers['x-request-id'] == 'abc-123'


def test_generates_request_id_when_absent(client: TestClient) -> None:
    response = client.get('/health')

    assert uuid.UUID(response.headers['x-request-id']).version == 4


def test_replaces_invalid_request_id(client: TestClient) -> None:
    response = client.get('/health', headers={'x-request-id': 'a b'})

    assert uuid.UUID(response.headers['x-request-id']).version == 4


def test_request_id_in_every_log_line(lines: list[str]) -> None:
    logger.info('before')
    TestClient(demo).get('/work', headers={'x-request-id': 'abc-123'})
    logger.info('after')

    assert lines[0] == '- before\n'
    assert lines[1] == 'abc-123 working\n'
    assert re.fullmatch(r'abc-123 GET /work 200 \d+\.\dms\n', lines[2])
    assert lines[3] == '- after\n'


def test_probes_are_not_logged(lines: list[str]) -> None:
    response = TestClient(demo).get('/live')

    assert response.headers['x-request-id']
    assert lines == []


def test_exception_reaches_fastapi_handler(lines: list[str]) -> None:
    client = TestClient(demo, raise_server_exceptions=False)
    response = client.get('/boom', headers={'x-request-id': 'abc-123'})

    assert response.status_code == 500
    assert response.json() == {'detail': 'handled: boom'}
    assert re.fullmatch(r'abc-123 GET /boom 500 \d+\.\dms\n', lines[0])


def test_uvicorn_access_log_is_off(lines: list[str]) -> None:
    logging.getLogger('uvicorn.access').info('%s - "GET /work"', '127.0.0.1')

    assert lines == []


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
