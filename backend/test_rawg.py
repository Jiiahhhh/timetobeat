import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAWG_API_KEY")

headers = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": os.getenv("RAWG_API_HOST", "rawg-video-games-database.p.rapidapi.com")
}

res = requests.get(
    "https://rawg-video-games-database.p.rapidapi.com/games",
    headers=headers,
    params={
        "search": "Hollow Knight",
        "page_size": "1"
    }
)

print(f"Status: {res.status_code}")
print(json.dumps(res.json(), indent=2))