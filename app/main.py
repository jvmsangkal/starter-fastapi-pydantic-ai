from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel
from sqlmodel import select

from app.agent import agent
from app.db import SessionDep, engine
from app.logging import setup_logging
from app.models import Item
from app.request_log import RequestLogMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    # Not at import time: `fastapi run app/main.py` imports this module before
    # uvicorn applies its log config, and that config would undo the setup.
    setup_logging()
    # str(URL) masks the password.
    logger.info('Using database {}', engine.url)
    yield


app = FastAPI(title='starter-fastapi-pydantic-ai', lifespan=lifespan)
app.add_middleware(RequestLogMiddleware)


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    output: str


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/chat')
async def chat(request: ChatRequest) -> ChatResponse:
    result = await agent.run(request.prompt)
    return ChatResponse(output=result.output)


@app.post('/items')
def create_item(item: Item, session: SessionDep) -> Item:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.get('/items')
def list_items(session: SessionDep) -> list[Item]:
    return list(session.exec(select(Item)).all())
