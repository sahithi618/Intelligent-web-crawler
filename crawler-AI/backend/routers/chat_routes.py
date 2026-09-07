from fastapi import APIRouter
from pydantic import BaseModel

from services.search_agent_service import SearchAgentService

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatInput(BaseModel):
    message: str


@router.post("/")
async def chat(input: ChatInput):
    result = await SearchAgentService.run_pipeline(input.message)
    return {
        "response": result["synthesized_answer"],
        "answer": result["synthesized_answer"],
        "intent": result["intent"],
        "key_points": result["key_points"],
        "sources": result["sources"],
        "action_prompt": result["action_prompt"],
    }
