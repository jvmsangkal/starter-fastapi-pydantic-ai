from pydantic_ai.models.test import TestModel

from app.agents.chat import agent


def test_agent_with_test_model() -> None:
    with agent.override(model=TestModel(custom_output_text='hello')):
        result = agent.run_sync('Say hello')

    assert result.output == 'hello'
