from fastapi import APIRouter
from schemas.request_models import RecommendRequest
from services.engine import get_recommendations

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "recommendations router is working"}

@router.get("/test-hltb/{game_name}")
async def test_hltb(game_name: str):
    from services.hltb import get_hltb_data
    return await get_hltb_data(game_name)

@router.post("/recommend")
def recommend(req: RecommendRequest):
    result = get_recommendations(req)
    return result