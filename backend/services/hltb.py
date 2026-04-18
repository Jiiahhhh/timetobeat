from howlongtobeatpy import HowLongToBeat

async def get_hltb_data(game_title: str) -> dict:
    try:
        results = await HowLongToBeat().async_search(game_title)
        
        if not results:
            return {"error": "No HLTB data found"}
        
        best = max(results, key=lambda x: x.similarity)
        
        # Only return if similarity is high enough
        if best.similarity < 0.5:
            return {"error": "No confident match found"}
        
        return {
            "title": best.game_name,
            "similarity": round(best.similarity, 2),
            "main_story": best.main_story,
            "main_extra": best.main_extra,
            "completionist": best.completionist
        }
    except Exception as e:
        return {"error": str(e)}