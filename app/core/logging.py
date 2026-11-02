import inspect
import json
import logging
import sys
import traceback
from typing import TYPE_CHECKING, Any

from loguru import logger

from app.core.env import env
from app.core.request_log import request_id

# loguru's default format with the request id after the level.
LOG_FORMAT = (
    '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
    '<level>{level: <8}</level> | '
    '{extra[request_id]} | '
    '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
    '<level>{message}</level>'
)

if TYPE_CHECKING:
    from loguru import Message


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Skip logging's own frames so loguru reports the original caller.
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = 'importlib' in filename and '_bootstrap' in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _json_sink(message: Message) -> None:
    record = message.record
    line: dict[str, Any] = {
        'time': record['time'].isoformat(),
        'level': record['level'].name,
        'message': record['message'],
        'location': f'{record["name"]}:{record["function"]}:{record["line"]}',
        'request_id': record['extra']['request_id'],
    }
    if record['exception'] is not None:
        line['exception'] = ''.join(traceback.format_exception(*record['exception']))
    sys.stderr.write(json.dumps(line) + '\n')


def setup_logging() -> None:
    logger.remove()
    logger.configure(
        patcher=lambda record: record['extra'].update(request_id=request_id.get())
    )
    if env.LOG_JSON:
        logger.add(_json_sink, level=env.LOG_LEVEL)
    else:
        logger.add(sys.stderr, level=env.LOG_LEVEL, format=LOG_FORMAT)
    logging.basicConfig(handlers=[InterceptHandler()], level=env.LOG_LEVEL, force=True)
    # uvicorn gives these loggers their own handlers and propagate=False.
    for name in ('uvicorn', 'uvicorn.error', 'uvicorn.access'):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.setLevel(logging.NOTSET)
    # RequestLogMiddleware writes the access log. uvicorn skips its own access
    # line when this logger has no handlers, so cut it off from the root's.
    logging.getLogger('uvicorn.access').propagate = False
