import logging
import logging.config
from collections.abc import Iterator

import pytest
from loguru import logger
from uvicorn.config import LOGGING_CONFIG

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


def test_stdlib_logs_go_through_loguru(lines: list[str]) -> None:
    logging.getLogger('uvicorn.access').info('%s - "GET /health"', '127.0.0.1')
    logging.getLogger('sqlalchemy').warning('pool exhausted')

    assert lines == [
        'INFO test_stdlib_logs_go_through_loguru: 127.0.0.1 - "GET /health"\n',
        'WARNING test_stdlib_logs_go_through_loguru: pool exhausted\n',
    ]
