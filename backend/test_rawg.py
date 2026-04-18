import requests
import json

RAPIDAPI_KEY = "1af6b54851msh823aa6511de0db6p13f989jsn59400668c149"

headers = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "rawg-video-games-database.p.rapidapi.com"
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