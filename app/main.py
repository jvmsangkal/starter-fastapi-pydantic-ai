from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.chat.routes import router as chat_router
from app.core.errors import AppError, app_error_handler
from app.core.logging import setup_logging
from app.core.probes import mark_ready
from app.core.probes import router as probes_router
from app.core.request_log import RequestLogMiddleware
from app.core.resources import open_resources
from app.items.routes import router as items_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Not at import time: `fastapi run app/main.py` imports this module before
    # uvicorn applies its log config, and that config would undo the setup.
    setup_logging()
    async with open_resources(app):
        with mark_ready(app):
            yield


def create_app() -> FastAPI:
    app = FastAPI(title='starter-fastapi-pydantic-ai', lifespan=lifespan)
    app.exception_handler(AppError)(app_error_handler)
    app.add_middleware(RequestLogMiddleware)
    app.include_router(probes_router)
    app.include_router(items_router, prefix='/v1')
    app.include_router(chat_router, prefix='/v1')
    return app


app = create_app()
