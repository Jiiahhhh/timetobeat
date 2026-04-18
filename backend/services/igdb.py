import os
import requests
from dotenv import load_dotenv

load_dotenv()

_access_token = None

def get_access_token() -> str:
    global _access_token
    if _access_token:
        return _access_token
    
    res = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": os.getenv("TWITCH_CLIENT_ID"),
            "client_secret": os.getenv("TWITCH_CLIENT_SECRET"),
            "grant_type": "client_credentials"
        }
    )
    _access_token = res.json()["access_token"]
    return _access_token

def get_igdb_data(game_title: str) -> dict:
    try:
        client_id = os.getenv("TWITCH_CLIENT_ID")
        token = get_access_token()
        
        headers = {
            "Client-ID": client_id,
            "Authorization": f"Bearer {token}"
        }
        query = f"""
            fields name, cover.image_id, genres.name, 
                   platforms.name, total_rating, summary;
            where name ~ *"{game_title}"*;
            limit 1;
        """
        res = requests.post(
            "https://api.igdb.com/v4/games",
            headers=headers,
            data=query
        )
        data = res.json()
        
        if not data:
            return {"error": "Game not found on IGDB"}
        
        g = data[0]
        cover_id = g.get("cover", {}).get("image_id")
        
        return {
            "title": g.get("name"),
            "cover_url": f"https://images.igdb.com/igdb/image/upload/t_cover_big/{cover_id}.jpg" if cover_id else None,
            "genres": [x["name"] for x in g.get("genres", [])],
            "platforms": [x["name"] for x in g.get("platforms", [])],
            "rating": round(g.get("total_rating", 0), 1),
            "summary": g.get("summary", "")
        }
    except Exception as e:
        return {"error": str(e)}