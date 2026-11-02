from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pydantic_ai import models

from app.main import app


@pytest.fixture(autouse=True)
def block_real_model_requests() -> Iterator[None]:
    with models.override_allow_model_requests(False):
        yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
