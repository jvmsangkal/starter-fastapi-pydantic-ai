from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pydantic_ai import models
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.db.base import metadata
from app.db.session import get_session
from app.main import app


@pytest.fixture(autouse=True)
def block_real_model_requests() -> Iterator[None]:
    with models.override_allow_model_requests(False):
        yield


@pytest.fixture
def session() -> Iterator[Session]:
    # StaticPool keeps a single connection so every thread sees the same in-memory DB.
    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
