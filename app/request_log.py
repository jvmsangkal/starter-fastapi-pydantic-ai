import re
import time
import uuid
from contextvars import ContextVar

from loguru import logger
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id: ContextVar[str] = ContextVar('request_id', default='-')

# Probe routes run every few seconds; an access line each would drown the log.
SKIPPED_PATHS = frozenset({'/live', '/ready'})
# An incoming id ends up in every log line, so accept only short, plain ones.
VALID_REQUEST_ID = re.compile(r'[A-Za-z0-9._:-]{1,128}')


class RequestLogMiddleware:
    """Tag each HTTP request with an x-request-id and log one access line for it."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        incoming = Headers(scope=scope).get('x-request-id', '')
        rid = incoming if VALID_REQUEST_ID.fullmatch(incoming) else str(uuid.uuid4())
        token = request_id.set(rid)
        # Stays 500 if the app raises before it starts a response.
        status = 500
        start = time.perf_counter()

        async def send_with_request_id(message: Message) -> None:
            nonlocal status
            if message['type'] == 'http.response.start':
                status = message['status']
                MutableHeaders(scope=message)['x-request-id'] = rid
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            if scope['path'] not in SKIPPED_PATHS:
                logger.info(
                    '{method} {path} {status} {duration_ms}ms',
                    method=scope['method'],
                    path=scope['path'],
                    status=status,
                    duration_ms=round((time.perf_counter() - start) * 1000, 1),
                )
            request_id.reset(token)
