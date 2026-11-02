from fastapi.testclient import TestClient
from pydantic_ai.models.test import TestModel

from app.agents.chat import agent


def test_chat_route(client: TestClient) -> None:
    with agent.override(model=TestModel(custom_output_text='hi there')):
        response = client.post('/v1/chat', json={'prompt': 'hi'})

    assert response.status_code == 200
    assert response.json() == {'output': 'hi there'}
