from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from sqlmodel import select

from app.agent import agent
from app.db import SessionDep, create_db_and_tables
from app.models import Item
from app.resources import open_resources


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    async with open_resources(app):
        create_db_and_tables(app.state.engine)
        yield


app = FastAPI(title='starter-fastapi-pydantic-ai', lifespan=lifespan)


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
