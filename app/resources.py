from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.agent import agent
from app.db import create_db_engine
from app.env import env


@asynccontextmanager
async def open_resources(app: FastAPI) -> AsyncGenerator[None]:
    engine = create_db_engine()
    app.state.engine = engine
    try:
        async with AsyncExitStack() as stack:
            # Without a key the model is a lazy string; entering the agent would build
            # the OpenAI provider and fail on the missing key.
            if env.OPENAI_API_KEY is not None:
                await stack.enter_async_context(agent)
            yield
    finally:
        engine.dispose()
        logger.info('Disposed database engine')
