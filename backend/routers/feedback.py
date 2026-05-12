from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.supabase_client import supabase

router = APIRouter()

class FeedbackRequest(BaseModel):
    game_id: int
    feedback: bool
    vibe: Optional[str] = None
    hours_available: Optional[float] = None
    platform: Optional[str] = None

@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    try:
        supabase.table("recommendation_feedback").insert({
            "game_id": req.game_id,
            "feedback": req.feedback,
            "vibe": req.vibe,
            "hours_available": req.hours_available,
            "platform": req.platform,
        }).execute()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}