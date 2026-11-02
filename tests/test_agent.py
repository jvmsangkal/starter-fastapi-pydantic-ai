from fastapi.testclient import TestClient
from pydantic_ai.models.test import TestModel

from app.agent import agent


def test_agent_with_test_model() -> None:
    with agent.override(model=TestModel(custom_output_text="hello")):
        result = agent.run_sync("Say hello")

    assert result.output == "hello"


def test_chat_route(client: TestClient) -> None:
    with agent.override(model=TestModel(custom_output_text="hi there")):
        response = client.post("/chat", json={"prompt": "hi"})

    assert response.status_code == 200
    assert response.json() == {"output": "hi there"}
