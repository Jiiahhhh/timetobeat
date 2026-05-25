from fastapi import APIRouter
from schemas.request_models import RecommendRequest
from services.engine import get_recommendations

router = APIRouter()

@router.get("/health")
def health_check():
    """
    Check the health of the recommendations router.
    """
    return {"status": "recommendations router is working"}

@router.get("/test-hltb/{game_name}")
async def test_hltb(game_name: str):
    """
    Test endpoint to fetch HLTB time data for a specific game name.
    """
    from services.hltb import get_hltb_data
    return await get_hltb_data(game_name)

@router.post("/recommend")
def recommend(req: RecommendRequest):
    """
    Generate game recommendations matching the criteria in RecommendRequest.
    """
    result = get_recommendations(req)
    return result