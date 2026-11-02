from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from sqlmodel import select

from app.agent import agent
from app.db import SessionDep, create_db_and_tables
from app.logging import setup_logging
from app.models import Item
from app.probes import mark_ready
from app.probes import router as probes_router
from app.request_log import RequestLogMiddleware
from app.resources import open_resources


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Not at import time: `fastapi run app/main.py` imports this module before
    # uvicorn applies its log config, and that config would undo the setup.
    setup_logging()
    async with open_resources(app):
        create_db_and_tables(app.state.engine)
        with mark_ready(app):
            yield


app = FastAPI(title='starter-fastapi-pydantic-ai', lifespan=lifespan)
app.add_middleware(RequestLogMiddleware)
app.include_router(probes_router)


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    output: str


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
