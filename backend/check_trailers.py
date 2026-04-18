import requests
import json

with open("data/games_seed.json", "r", encoding="utf-8") as f:
    games = json.load(f)

print("Checking trailer IDs...\n")
print(f"{'STATUS':<10} {'TITLE':<45} {'ID'}")
print("-" * 80)

invalid = []
valid = []

for game in games:
    yt_id = game.get("trailer_youtube_id")
    title = game.get("title", "Unknown")

    if not yt_id:
        print(f"{'⚠️  NO ID':<10} {title:<45} -")
        invalid.append({"title": title, "id": None})
        continue

    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={yt_id}&format=json"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            print(f"{'✅ VALID':<10} {title:<45} {yt_id}")
            valid.append(title)
        else:
            print(f"{'❌ INVALID':<10} {title:<45} {yt_id}")
            invalid.append({"title": title, "id": yt_id})
    except Exception as e:
        print(f"{'⚠️  ERROR':<10} {title:<45} {yt_id}")
        invalid.append({"title": title, "id": yt_id})

print("-" * 80)
print(f"\n✅ Valid   : {len(valid)}")
print(f"❌ Invalid : {len(invalid)}")