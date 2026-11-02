from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, FastAPI, Request, Response, status

router = APIRouter()


@contextmanager
def mark_ready(app: FastAPI) -> Iterator[None]:
    """Report `/ready` as 200 while the body runs and 503 before and after."""
    app.state.ready = True
    try:
        yield
    finally:
        app.state.ready = False


@router.get('/live', include_in_schema=False)
def live() -> dict[str, str]:
    return {'status': 'ok'}


@router.get('/ready', include_in_schema=False)
def ready(request: Request, response: Response) -> dict[str, str]:
    if not getattr(request.app.state, 'ready', False):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {'status': 'unavailable'}
    return {'status': 'ok'}
