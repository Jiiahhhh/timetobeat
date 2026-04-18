import json
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

with open("data/games_seed.json", "r", encoding="utf-8") as f:
    games = json.load(f)

# Remove duplicates by id
seen = set()
unique_games = []
for game in games:
    if game["id"] not in seen:
        seen.add(game["id"])
        unique_games.append(game)

print(f"Seeding {len(unique_games)} games...")

# Insert in batches of 20
batch_size = 20
for i in range(0, len(unique_games), batch_size):
    batch = unique_games[i:i + batch_size]
    res = supabase.table("games").insert(batch).execute()
    print(f"Inserted batch {i//batch_size + 1} — {len(batch)} games")

print("Seeding complete!")