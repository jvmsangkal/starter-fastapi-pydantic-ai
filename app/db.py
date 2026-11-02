from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from app.env import env

# SQLite connections are thread-bound by default; FastAPI runs sync deps in a threadpool.
connect_args = (
    {'check_same_thread': False} if env.DATABASE_URL.startswith('sqlite') else {}
)
engine = create_engine(env.DATABASE_URL, connect_args=connect_args)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
