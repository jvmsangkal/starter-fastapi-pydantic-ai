from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.agents.chat import agent
from app.core.env import env
from app.db.session import create_db_engine


@asynccontextmanager
async def open_resources(app: FastAPI) -> AsyncGenerator[None]:
    engine = create_db_engine()
    app.state.engine = engine
    # str(URL) masks the password.
    logger.info('Opened database engine for {}', engine.url)
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
