from howlongtobeatpy import HowLongToBeat

async def get_hltb_data(game_title: str) -> dict:
    """
    Search HowLongToBeat for the specified game title.
    Returns estimated play hours for main story, main+extra, and completionist,
    filtering for similarity above a confidence threshold (0.5).
    """
    try:
        results = await HowLongToBeat().async_search(game_title)
        
        if not results:
            return {"error": "No HLTB data found"}
        
        best = max(results, key=lambda x: x.similarity)
        
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