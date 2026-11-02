from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.env import env

MODEL_NAME = 'gpt-5.4-mini'

# pydantic-ai only looks for OPENAI_API_KEY in os.environ, so a key loaded from .env
# has to be passed explicitly. Without a key, defer_model_check lets the app import and
# boot; POST /chat then fails with pydantic-ai's "set OPENAI_API_KEY" error.
model: Model | str = f'openai:{MODEL_NAME}'
if env.OPENAI_API_KEY is not None:
    model = OpenAIResponsesModel(
        MODEL_NAME,
        provider=OpenAIProvider(api_key=env.OPENAI_API_KEY.get_secret_value()),
    )

agent = Agent(
    model,
    instructions='You are a concise, helpful assistant.',
    defer_model_check=True,
)
