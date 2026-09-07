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
        "confidence_score": result["confidence_score"],
        "confidence_level": result["confidence_level"],
        "key_points": result["key_points"],
        "actionable": result["actionable"],
        "action_type": result["action_type"],
        "action_prompt": result["action_prompt"],
        "actionable_steps": result["actionable_steps"],
        "follow_up_questions": result["follow_up_questions"],
        "jobs": result["jobs"],
        "products": result["products"],
        "events": result["events"],
        "sources": result["sources"],
    }
