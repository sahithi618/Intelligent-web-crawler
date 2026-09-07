import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.search_agent_service import SearchAgentService
from auth import get_current_user
from models import UserHistory
from database import SessionLocal

router = APIRouter(prefix="/detect", tags=["Detection"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class NewsInput(BaseModel):
    text: str


@router.post("/analyze")
async def detect_text_detailed(
    body: NewsInput,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    input_text = body.text.strip()
    if not input_text:
        return {"error": "Please enter a search query or question."}

    try:
        pipeline_result = await SearchAgentService.run_pipeline(input_text)

        user_friendly = {
            "status": f"Found results (Intent: {pipeline_result['intent'].upper()})",
            "confidence_score": pipeline_result["confidence_score"],
            "confidence_level": pipeline_result["confidence_level"],
            "summary": pipeline_result["summary"],
            "recommendation": pipeline_result["recommendation"],
            "key_claim": pipeline_result["key_claim"],
            "key_claim_verdict": pipeline_result["key_claim_verdict"],
            "key_claim_reason": pipeline_result["key_claim_reason"],
            "note": pipeline_result["note"],
        }

        history_entry = UserHistory(
            user_id=user,
            input_text=input_text,
            result=json.dumps(user_friendly),
        )
        db.add(history_entry)
        db.commit()

        return {
            "research_verdict": pipeline_result,
            "combined_score": pipeline_result["confidence_score"],
            "recommendation": pipeline_result["action_prompt"],
            "user_friendly": user_friendly,
            "synthesized_answer": pipeline_result["synthesized_answer"],
            "key_points": pipeline_result["key_points"],
            "actionable": pipeline_result["actionable"],
            "action_type": pipeline_result["action_type"],
            "action_prompt": pipeline_result["action_prompt"],
            "actionable_steps": pipeline_result["actionable_steps"],
            "follow_up_questions": pipeline_result["follow_up_questions"],
            "jobs": pipeline_result["jobs"],
            "products": pipeline_result.get("products", []),
            "events": pipeline_result.get("events", []),
            "sources": pipeline_result["sources"],
            "intent": pipeline_result["intent"],
        }
    except Exception as exc:
        db.rollback()
        print(f"Error during intelligent crawl: {exc}")
        return {
            "research_verdict": {"error": "Analysis failed due to service error"},
            "combined_score": None,
            "recommendation": "Please try again.",
            "user_friendly": {
                "status": "Analysis failed",
                "confidence_level": "low",
                "summary": "An internal error occurred. Please try again later.",
                "note": "If this issue persists, report it to support.",
            },
            "error": str(exc),
        }


@router.get("/history")
def get_user_history(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        history = (
            db.query(UserHistory)
            .filter(UserHistory.user_id == user)
            .order_by(UserHistory.id.desc())
            .all()
        )
        return [
            {
                "id": item.id,
                "input_text": item.input_text,
                "result": json.loads(item.result),
            }
            for item in history
        ]
    except Exception as exc:
        return {"error": str(exc)}
