from pydantic_ai import Agent

# defer_model_check lets the app import and boot without OPENAI_API_KEY;
# the key is only required when the agent actually calls the model.
agent = Agent(
    "openai:gpt-5.4-mini",
    instructions="You are a concise, helpful assistant.",
    defer_model_check=True,
)
