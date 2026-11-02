from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.env import env


def create_db_engine() -> Engine:
    # SQLite connections are thread-bound by default; FastAPI runs sync deps in a threadpool.
    connect_args = (
        {'check_same_thread': False} if env.DATABASE_URL.startswith('sqlite') else {}
    )
    return create_engine(env.DATABASE_URL, connect_args=connect_args)


def create_db_and_tables(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
