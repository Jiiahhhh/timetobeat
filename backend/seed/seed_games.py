"""
seed_games.py
-------------
Seeding script to expand the TimeToBeat database from 97 → 1000 games.

Sources:
- Steam Search API      → list of popular games (sorted by reviews)
- Steam appdetails API  → cover, description, genres, platforms, metacritic, is_coop
- Steam Deck API        → Steam Deck verified check
- SteamSpy API          → tags for genre mapping + difficulty heuristic
- howlongtobeatpy       → hltb_main, hltb_extra, hltb_completionist

Requirements:
    pip install requests howlongtobeatpy supabase python-dotenv

Usage:
    # Test mode first (5 games)
    python seed_games.py --test

    # Full run
    python seed_games.py
"""

import asyncio
import argparse
import time
import re
import os
import requests
from howlongtobeatpy import HowLongToBeat
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")  # service role key
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# GENRE MAPPING — Steam/SteamSpy tags → TTB labels
# ============================================================
GENRE_TAG_MAP = {
    # → Action
    "Action": "Action",
    "Shooter": "Action",
    "FPS": "Action",
    "Third-Person Shooter": "Action",
    "Fighting": "Action",
    "Hack and Slash": "Action",
    "Action Roguelike": "Action",
    "Beat 'em up": "Action",
    "Tower Defense": "Action",
    "Battle Royale": "Action",
    "Stealth": "Action",

    # → Story
    "Story Rich": "Story",
    "Visual Novel": "Story",
    "Adventure": "Story",
    "Interactive Fiction": "Story",
    "Walking Simulator": "Story",
    "Narrative": "Story",
    "Point & Click": "Story",
    "Mystery": "Story",
    "Horror": "Story",
    "Psychological Horror": "Story",
    "Thriller": "Story",

    # → RPG
    "RPG": "RPG",
    "Action RPG": "RPG",
    "JRPG": "RPG",
    "Turn-Based RPG": "RPG",
    "CRPG": "RPG",
    "Tactical RPG": "RPG",
    "Dungeon Crawler": "RPG",
    "Roguelike": "RPG",
    "Rogue-lite": "RPG",

    # → Puzzle
    "Puzzle": "Puzzle",
    "Strategy": "Puzzle",
    "Turn-Based Strategy": "Puzzle",
    "City Builder": "Puzzle",
    "Management": "Puzzle",
    "Logic": "Puzzle",
    "Escape Room": "Puzzle",
    "4X": "Puzzle",
    "Grand Strategy": "Puzzle",

    # → Relaxed
    "Simulation": "Relaxed",
    "Casual": "Relaxed",
    "Farming Sim": "Relaxed",
    "Relaxing": "Relaxed",
    "Cozy": "Relaxed",
    "Exploration": "Relaxed",
    "Sandbox": "Relaxed",
    "Sports": "Relaxed",
    "Racing": "Relaxed",
    "Fishing": "Relaxed",
    "Life Sim": "Relaxed",
    "Crafting": "Relaxed",

    # → Classic (mostly manual, but flagged if these tags exist)
    "Retro": "Classic",
    "Pixel Graphics": "Classic",
    "Old School": "Classic",
    "8-Bit": "Classic",
    "16-bit": "Classic",
}

# Tags for is_coop detection
COOP_TAGS = {
    "Co-op", "Online Co-Op", "Local Co-Op",
    "Co-operative", "Split Screen", "Local Multiplayer"
}

# Tags for difficulty heuristic
DIFFICULTY_MAP = {
    "Souls-like": 5,
    "Difficult": 4,
    "Hard": 4,
    "Challenging": 4,
    "Rogue-like": 4,
    "Rogue-lite": 4,
    "Action Roguelike": 4,
    "Relaxing": 2,
    "Casual": 2,
    "Cozy": 1,
    "Easy": 1,
}


# ============================================================
# STEAM FUNCTIONS
# ============================================================

def get_popular_app_ids(total: int = 1000) -> list[int]:
    """
    Get a list of popular App IDs from two sources:
    1. Steam Top Sellers — mainstream games with high sales
    2. Steam Most Reviewed — games heavily played and reviewed

    Merge + deduplicate, prioritizing games that appear in both lists.
    """
    import re

    def fetch_from_steam(params: dict, target: int) -> list[int]:
        app_ids = []
        page = 0
        count = 100

        while len(app_ids) < target:
            p = {**params, "json": 1, "category1": 998, "start": page * count, "count": count}
            try:
                r = requests.get(
                    "https://store.steampowered.com/search/results/",
                    params=p,
                    timeout=10
                )
                data = r.json()
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    logo = item.get("logo", "")
                    match = re.search(r'/apps/(\d+)/', logo)
                    if match:
                        app_ids.append(int(match.group(1)))

                print(f"    Page {page + 1}: {len(items)} games (total: {len(app_ids)})")
                page += 1
                time.sleep(1)

            except Exception as e:
                print(f"    Error page {page}: {e}")
                break

        return app_ids[:target]

    # Fetch from two sources
    print("Fetching List 1 — Steam Top Sellers...")
    top_sellers = fetch_from_steam({"filter": "topsellers", "os": "win"}, total)

    print("\nFetching List 2 — Steam Most Reviewed...")
    most_reviewed = fetch_from_steam({"sort_by": "Reviews_DESC", "os": "win"}, total)

    # Merge with priority
    # Games appearing in both lists = most popular, placed first
    set_sellers = set(top_sellers)
    set_reviewed = set(most_reviewed)

    both = [aid for aid in top_sellers if aid in set_reviewed]
    only_sellers = [aid for aid in top_sellers if aid not in set_reviewed]
    only_reviewed = [aid for aid in most_reviewed if aid not in set_sellers]

    merged = both + only_sellers + only_reviewed

    print(f"\nMerge result:")
    print(f"  In both lists     : {len(both)}")
    print(f"  Top sellers only  : {len(only_sellers)}")
    print(f"  Most reviewed only: {len(only_reviewed)}")
    print(f"  Total unique      : {len(merged)}")

    return merged[:total * 2]  # return extra because many will be skipped


def get_steam_details(app_id: int) -> dict | None:
    """Fetch game details from Steam appdetails API."""
    try:
        url = "https://store.steampowered.com/api/appdetails"
        params = {"appids": app_id, "key": STEAM_API_KEY}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        app_data = data.get(str(app_id), {})
        if not app_data.get("success"):
            return None

        d = app_data["data"]

        # Skip if not a game
        if d.get("type") != "game":
            return None

        return d

    except Exception as e:
        print(f"    Steam appdetails error: {e}")
        return None


def get_steam_deck_verified(app_id: int) -> bool:
    """Check Steam Deck Verified status."""
    try:
        url = "https://store.steampowered.com/saleaction/ajaxgetdeckappcompatibilityreport"
        r = requests.get(url, params={"nAppID": app_id}, timeout=10)
        data = r.json()
        return data.get("results", {}).get("resolved_category") == 3
    except Exception:
        return False


def get_steamspy_data(app_id: int) -> dict:
    try:
        url = "https://steamspy.com/api.php"
        r = requests.get(url, params={"request": "appdetails", "appid": app_id}, timeout=10)
        data = r.json()
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def parse_platforms(steam_data: dict, deck_verified: bool) -> list[str]:
    """Parse platforms from Steam data."""
    platforms_raw = steam_data.get("platforms", {})
    platforms = []
    if platforms_raw.get("windows"):
        platforms.append("Windows")
    if platforms_raw.get("mac"):
        platforms.append("Mac")
    if platforms_raw.get("linux"):
        platforms.append("Linux")
    if deck_verified:
        platforms.append("Steam Deck")
    return platforms if platforms else ["Windows"]


def parse_genres(steam_data: dict, steamspy_tags: dict) -> list[str]:
    """Map Steam genres + SteamSpy tags into TTB genre labels."""
    genres = set()

    # From Steam genres
    for g in steam_data.get("genres", []):
        desc = g.get("description", "")
        if desc in GENRE_TAG_MAP:
            genres.add(GENRE_TAG_MAP[desc])

    # From SteamSpy tags (more detailed)
    for tag in steamspy_tags.keys():
        if tag in GENRE_TAG_MAP:
            genres.add(GENRE_TAG_MAP[tag])

    # If no genre detected, fallback from categories
    if not genres:
        for cat in steam_data.get("categories", []):
            if "RPG" in cat.get("description", ""):
                genres.add("RPG")

    return list(genres) if genres else ["Action"]


def parse_is_coop(steam_data: dict, steamspy_tags: dict) -> bool:
    """Detect co-op from Steam categories and SteamSpy tags."""
    # From Steam categories
    for cat in steam_data.get("categories", []):
        if cat.get("id") in [9, 38]:
            return True

    # From SteamSpy tags
    for tag in steamspy_tags.keys():
        if tag in COOP_TAGS:
            return True

    return False


def parse_difficulty(steamspy_tags: dict) -> int:
    """Weighted difficulty based on SteamSpy tag count."""
    tag_scores = {
        "Souls-like": 5,
        "Difficult": 4,
        "Hard": 4,
        "Challenging": 4,
        "Rogue-like": 4,
        "Rogue-lite": 4,
        "Action Roguelike": 4,
        "Roguelike": 4,
        "Relaxing": 2,
        "Casual": 2,
        "Cozy": 1,
        "Easy": 1,
        "Family Friendly": 1,
    }

    total_weight = 0
    weighted_score = 0

    for tag, score in tag_scores.items():
        if tag in steamspy_tags:
            count = steamspy_tags[tag]
            weighted_score += score * count
            total_weight += count

    if total_weight == 0:
        return 3
    return round(weighted_score / total_weight)


def round_hltb(hours: float) -> float:
    """Round to nearest 0.5 hour. Example: 6.9 → 7.0, 6.3 → 6.5"""
    return round(hours * 2) / 2


# ============================================================
# HLTB FUNCTION
# ============================================================

async def get_hltb_data(title: str) -> dict | None:
    """Fetch HLTB data via howlongtobeatpy."""
    clean_title = title.replace("™", "").replace("®", "").strip()
    try:
        results = await HowLongToBeat().async_search(clean_title)
        if not results:
            return None

        best = max(results, key=lambda g: g.similarity)

        # Reject if similarity is too low
        if best.similarity < 0.6:
            return None

        main = best.main_story
        mp = best.mp_time

        # Exclude pure competitive multiplayer
        # main_story exists but no main_extra = likely "Vs." data
        if main and main > 0 and mp and mp > 0 and not best.main_extra:
            return None

        # Must have at least hltb_main
        if not main or main <= 0:
            return None

        return {
            "hltb_main": round_hltb(main),
            "hltb_extra": round_hltb(best.main_extra) if best.main_extra and best.main_extra > 0 else None,
            "hltb_completionist": round_hltb(best.completionist) if best.completionist and best.completionist > 0 else None,
        }

    except Exception as e:
        print(f"    HLTB error: {e}")
        return None


# ============================================================
# HELPER
# ============================================================

def get_existing_games() -> list[dict]:
    """Get all existing games with id, steam_app_id, rating, and title using pagination."""
    try:
        games = []
        limit = 1000
        offset = 0
        while True:
            res = supabase.table("games").select("id, steam_app_id, rating, title").range(offset, offset + limit - 1).execute()
            data = res.data
            if not data:
                break
            games.extend(data)
            if len(data) < limit:
                break
            offset += limit
        return games
    except Exception as e:
        print(f"Error fetching existing games: {e}")
        return []


def clean_description(text: str) -> str:
    """Remove HTML tags from Steam description."""
    clean = re.sub(r'<[^>]+>', '', text or '')
    clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&#39;', "'")
    return clean.strip()[:500]


# ============================================================
# MAIN SEEDING LOGIC
# ============================================================

async def seed(test_mode: bool = False):
    print("=" * 60)
    print("TimeToBeat — Game Seeding Script")
    print(f"Mode: {'TEST (5 games)' if test_mode else 'FULL (up to 1200 games)'}")
    print("=" * 60)

    # Check existing data
    existing_games = get_existing_games()
    existing_ids = {row["steam_app_id"] for row in existing_games if row.get("steam_app_id")}
    print(f"\nExisting games in DB: {len(existing_games)}")

    # Fetch popular game list
    target = 50 if test_mode else 1500
    app_ids = get_popular_app_ids(target)
    print(f"App IDs fetched: {len(app_ids)}")

    inserted_or_replaced = 0
    skipped_existing = 0
    skipped_no_hltb = 0
    skipped_error = 0
    max_insert = 5 if test_mode else 1200

    print(f"\nStarting processing...\n")

    for i, app_id in enumerate(app_ids):
        # Terminate if we have performed max operations
        if inserted_or_replaced >= max_insert:
            print(f"\nReached max operations limit of {max_insert}. Stopping.")
            break

        # Skip if already exists
        if app_id in existing_ids:
            skipped_existing += 1
            continue

        print(f"[{i+1}/{len(app_ids)}] App ID: {app_id}")

        # 1. Fetch Steam details
        steam_data = get_steam_details(app_id)
        if not steam_data:
            print(f"  SKIP — not a game or Steam error")
            skipped_error += 1
            time.sleep(0.5)
            continue

        title = steam_data.get("name", "")
        title_clean = title.encode('ascii', errors='replace').decode('ascii')
        print(f"  Title: {title_clean}")

        # 2. Fetch HLTB
        hltb = await get_hltb_data(title)
        if not hltb:
            print(f"  SKIP — no HLTB data")
            skipped_no_hltb += 1
            time.sleep(1)
            continue

        print(f"  HLTB: main={hltb['hltb_main']}hrs, extra={hltb['hltb_extra']}hrs")

        # 3. Fetch Steam Deck
        deck_verified = get_steam_deck_verified(app_id)

        # 4. Fetch SteamSpy tags and review data
        steamspy_data = get_steamspy_data(app_id)
        steamspy_tags = steamspy_data.get("tags", {}) if isinstance(steamspy_data.get("tags"), dict) else {}

        # 5. Determine and estimate rating
        metacritic = steam_data.get("metacritic", {})
        rating = metacritic.get("score") if metacritic else None
        rating_source = "Metacritic"

        if rating is None:
            pos = steamspy_data.get("positive", 0)
            neg = steamspy_data.get("negative", 0)
            total_revs = pos + neg
            if total_revs >= 30:
                rating = int((pos / total_revs) * 100)
                rating_source = f"Steam reviews ({pos}/{total_revs} positive)"
            else:
                print(f"  SKIP — no Metacritic rating and insufficient Steam reviews ({total_revs} reviews)")
                skipped_no_hltb += 1
                time.sleep(1)
                continue

        print(f"  Rating: {rating} (Source: {rating_source})")

        # 6. Parse all other fields
        platforms = parse_platforms(steam_data, deck_verified)
        genres = parse_genres(steam_data, steamspy_tags)
        is_coop = parse_is_coop(steam_data, steamspy_tags)
        difficulty = parse_difficulty(steamspy_tags)
        cover_url = steam_data.get("header_image", "")
        cover_portrait_url = cover_url.replace("header.jpg", "library_600x900.jpg") if cover_url else ""
        short_desc = clean_description(steam_data.get("short_description", ""))

        row = {
            "title": title,
            "cover_url": cover_url,
            "cover_portrait_url": cover_portrait_url,
            "genres": genres,
            "platforms": platforms,
            "rating": rating,
            "hltb_main": hltb["hltb_main"],
            "hltb_extra": hltb["hltb_extra"],
            "hltb_completionist": hltb["hltb_completionist"],
            "short_description": short_desc,
            "steam_app_id": app_id,
            "trailer_youtube_id": None,
            "trailer_valid": False,
            "difficulty": difficulty,
            "is_coop": is_coop,
        }

        # 7. Check database limit and find worst game if pruning is needed
        db_size = len(existing_games)
        worst_game = None
        worst_rating = None

        if db_size >= 1200:
            # Find the worst game in the database
            # Treat existing None ratings in the database as 70.0
            def get_rating_value(g):
                r = g.get("rating")
                return float(r) if r is not None else 70.0
            
            worst_game = min(existing_games, key=get_rating_value)
            worst_rating = get_rating_value(worst_game)

            # Compare rating
            if float(rating) <= worst_rating:
                worst_title_clean = worst_game['title'].encode('ascii', errors='replace').decode('ascii')
                print(f"  SKIP — Candidate rating ({rating}) is not better than the worst game in DB ({worst_title_clean} with rating {worst_rating})")
                time.sleep(1)
                continue

        # 8. Delete worst game if replacement is triggered, then insert the new game
        try:
            if worst_game is not None:
                worst_title_clean = worst_game['title'].encode('ascii', errors='replace').decode('ascii')
                print(f"  [REPLACING] Deleting worst game: {worst_title_clean} (Rating: {worst_rating})")
                supabase.table("games").delete().eq("id", worst_game["id"]).execute()
                # Update local cache
                existing_games = [g for g in existing_games if g["id"] != worst_game["id"]]
                if worst_game.get("steam_app_id") in existing_ids:
                    existing_ids.remove(worst_game["steam_app_id"])

            # Insert new game
            supabase.table("games").insert(row).execute()
            print(f"  [INSERTED] — genres: {genres}, platforms: {platforms}, difficulty: {difficulty}, coop: {is_coop}")
            
            # Fetch newly inserted ID to keep local cache accurate
            inserted_id = None
            try:
                res_insert = supabase.table("games").select("id").eq("steam_app_id", app_id).execute()
                if res_insert.data:
                    inserted_id = res_insert.data[0]["id"]
            except Exception:
                pass

            existing_games.append({
                "id": inserted_id or 999999,
                "steam_app_id": app_id,
                "rating": rating,
                "title": title
            })
            existing_ids.add(app_id)
            inserted_or_replaced += 1

        except Exception as e:
            print(f"  [DATABASE ERROR] during replace/insert: {e}")
            skipped_error += 1

        # Delay to avoid hammering APIs
        time.sleep(2)

    # Summary
    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print(f"  Operations     : {inserted_or_replaced}")
    print(f"  Skip (exists)  : {skipped_existing}")
    print(f"  Skip (no HLTB) : {skipped_no_hltb}")
    print(f"  Skip (error)   : {skipped_error}")
    print("=" * 60)

    if test_mode and inserted_or_replaced > 0:
        print("\nTest mode done. Check results in Supabase first.")
        print("If data looks correct, run full mode:")
        print("  python seed_games.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Test mode: only insert 5 games")
    args = parser.parse_args()

    asyncio.run(seed(test_mode=args.test))