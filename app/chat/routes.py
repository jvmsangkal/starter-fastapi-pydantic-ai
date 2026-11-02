from fastapi import APIRouter

from app.agents.chat import agent
from app.chat.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix='/chat')


@router.post('')
async def chat(request: ChatRequest) -> ChatResponse:
    result = await agent.run(request.prompt)
    return ChatResponse(output=result.output)
