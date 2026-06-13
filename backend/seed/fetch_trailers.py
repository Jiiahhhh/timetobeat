"""
fetch_trailers.py
-----------------
Fetches YouTube trailer IDs for games in the TimeToBeat database
that currently have no trailer (trailer_youtube_id = null).

Flow:
1. Fetch all games with trailer_youtube_id = null from Supabase
2. Try to find the trailer on IGDB first (free, no quota limit)
3. If not found, search YouTube API for "{title} official trailer"
4. Update DB: set trailer_youtube_id and trailer_valid. 
   - Games with no trailer found are marked with empty string "" and trailer_valid = false
   - This creates a self-cleaning queue and prevents reprocessing them.

Requirements:
    pip install requests supabase python-dotenv

Usage:
    # Test mode (5 games only)
    python fetch_trailers.py --test

    # Full run
    python fetch_trailers.py
"""

import argparse
import time
import os
import sys
from pathlib import Path
import requests
from supabase import create_client
from dotenv import load_dotenv

# Add backend root to sys.path so we can import services
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")  # service role key
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# Delay between requests to avoid hammering APIs (seconds)
REQUEST_DELAY = 1.5


# ============================================================
# CUSTOM EXCEPTIONS FOR YOUTUBE QUOTA
# ============================================================

class QuotaExceededException(Exception):
    pass


class InvalidApiKeyException(Exception):
    pass


# ============================================================
# IGDB API FUNCTION (FREE SEARCH)
# ============================================================

def get_trailer_from_igdb(title: str) -> str | None:
    """
    Query IGDB API for a game's YouTube trailer ID.
    Uses twitch credentials if set in .env.
    """
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    try:
        from services.igdb import get_access_token
        token = get_access_token()

        headers = {
            "Client-ID": client_id,
            "Authorization": f"Bearer {token}"
        }

        # Escape double quotes for IGDB query syntax
        clean_title = title.replace('"', '\\"')
        query = f'fields name, videos.video_id, videos.name; search "{clean_title}"; limit 1;'
        res = requests.post(
            "https://api.igdb.com/v4/games",
            headers=headers,
            data=query,
            timeout=10
        )

        if res.status_code != 200:
            return None

        data = res.json()
        if not data:
            return None

        game = data[0]
        videos = game.get("videos", [])
        if not videos:
            return None

        # Try to find a video containing "trailer" in the name
        for video in videos:
            name = video.get("name", "").lower()
            if "trailer" in name:
                return video.get("video_id")

        # Fallback to the first video available
        return videos[0].get("video_id")

    except Exception as e:
        print(f"    IGDB search error: {e}")
        return None


# ============================================================
# YOUTUBE FUNCTIONS
# ============================================================

def search_trailer(title: str) -> str | None:
    """
    Search YouTube for a game trailer.
    Tries "{title} game official trailer" restricted to Gaming category (ID 20).
    Returns YouTube video ID or None.
    """
    query = f"{title} game official trailer"
    try:
        params = {
            "part": "id",
            "q": query,
            "type": "video",
            "videoCategoryId": "20",  # Restrict search to Gaming category
            "maxResults": 1,
            "key": YOUTUBE_API_KEY,
        }
        r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
        data = r.json()

        # Check for API errors
        if "error" in data:
            error_msg = data["error"]["message"]
            print(f"    YouTube API error: {error_msg}")
            
            # Raise custom exceptions for specific critical errors
            if "quota" in error_msg.lower() or "limit" in error_msg.lower():
                raise QuotaExceededException(error_msg)
            elif "key" in error_msg.lower() or "invalid" in error_msg.lower():
                raise InvalidApiKeyException(error_msg)
            return None

        items = data.get("items", [])
        if items:
            video_id = items[0]["id"]["videoId"]
            print(f"    Found via YouTube query: '{query}' -> {video_id}")
            return video_id

    except (QuotaExceededException, InvalidApiKeyException):
        raise
    except Exception as e:
        print(f"    Search error: {e}")
        return None

    return None


# ============================================================
# SUPABASE FUNCTIONS
# ============================================================

def check_youtube_videos(video_ids: list[str]) -> dict[str, dict]:
    """
    Query YouTube API for status and details of multiple video IDs.
    Returns a dict mapping video_id -> { "exists": bool, "valid": bool, "title": str, "category_id": str }
    """
    if not video_ids or not YOUTUBE_API_KEY:
        return {}

    results = {}
    # YouTube allows max 50 IDs per request
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        ids_str = ",".join(batch)
        params = {
            "part": "snippet",
            "id": ids_str,
            "key": YOUTUBE_API_KEY,
        }
        try:
            r = requests.get("https://www.googleapis.com/youtube/v3/videos", params=params, timeout=10)
            data = r.json()
            if "error" in data:
                error_msg = data["error"]["message"]
                print(f"    YouTube API error: {error_msg}")
                # If quota error, raise it
                if "quota" in error_msg.lower() or "limit" in error_msg.lower():
                    raise QuotaExceededException(error_msg)
                continue

            items = data.get("items", [])
            found_ids = set()
            for item in items:
                v_id = item["id"]
                found_ids.add(v_id)
                snippet = item.get("snippet", {})
                title = snippet.get("title", "")
                cat_id = snippet.get("categoryId", "")

                # Check if it is in Gaming category (20)
                is_valid = (cat_id == "20")
                results[v_id] = {
                    "exists": True,
                    "valid": is_valid,
                    "title": title,
                    "category_id": cat_id
                }

            # For IDs not returned by YouTube, they are deleted/private (invalid)
            for v_id in batch:
                if v_id not in found_ids:
                    results[v_id] = {
                        "exists": False,
                        "valid": False,
                        "title": "[DELETED/PRIVATE/INVALID ID]",
                        "category_id": ""
                    }
        except QuotaExceededException:
            raise
        except Exception as e:
            print(f"    Error checking video batch: {e}")

    return results


def get_games_without_trailer(limit: int = 1000) -> list[dict]:
    """Fetch games that have no trailer_youtube_id set."""
    try:
        res = (
            supabase.table("games")
            .select("id, title")
            .is_("trailer_youtube_id", "null")
            .order("id")
            .limit(limit)
            .execute()
        )
        return res.data
    except Exception as e:
        print(f"Error fetching games: {e}")
        return []


def get_games_with_trailer(limit: int = 1000) -> list[dict]:
    """Fetch games that currently have a non-empty trailer_youtube_id set."""
    try:
        res = (
            supabase.table("games")
            .select("id, title, trailer_youtube_id")
            .neq("trailer_youtube_id", "")
            .not_.is_("trailer_youtube_id", "null")
            .order("id")
            .limit(limit)
            .execute()
        )
        return res.data
    except Exception as e:
        print(f"Error fetching games with trailers: {e}")
        return []


def update_trailer(game_id: int, youtube_id: str, valid: bool) -> bool:
    """Update trailer fields for a game."""
    try:
        supabase.table("games").update({
            "trailer_youtube_id": youtube_id,
            "trailer_valid": valid,
        }).eq("id", game_id).execute()
        return True
    except Exception as e:
        print(f"    DB update error: {e}")
        return False


# ============================================================
# MAIN LOGIC
# ============================================================

def run(test_mode: bool = False, dry_run: bool = False, query_test: str | None = None, validate_mode: bool = False):
    if validate_mode:
        print("=" * 60)
        print("TimeToBeat - Existing Trailer Validator")
        print(f"Mode  : {'TEST (20 games)' if test_mode else 'FULL'}")
        if dry_run:
            print("Dry Run: Active (No database updates will be made)")
        print("=" * 60)

        if not YOUTUBE_API_KEY:
            print("\n[ERROR] YOUTUBE_API_KEY not configured. Cannot perform validation.\n")
            return

        limit = 20 if test_mode else 10000
        games = get_games_with_trailer(limit=limit)

        print(f"\nGames with existing trailers: {len(games)}")
        if not games:
            print("No games with trailers to validate. All done!")
            return

        # Extract unique video IDs to check
        video_ids = list(set([g["trailer_youtube_id"] for g in games if g.get("trailer_youtube_id")]))
        print(f"Unique YouTube Video IDs to validate: {len(video_ids)}")

        print("\nValidating videos via YouTube API...")
        try:
            yt_status = check_youtube_videos(video_ids)
        except QuotaExceededException:
            print("\n[ERROR] YouTube API quota limit reached during validation!")
            return
        except Exception as e:
            print(f"\n[ERROR] Validation failed: {e}")
            return

        invalidated_count = 0
        deleted_count = 0
        wrong_category_count = 0

        print("\nAnalyzing results:")
        for i, game in enumerate(games):
            game_id = game["id"]
            title = game["title"]
            v_id = game["trailer_youtube_id"]

            status = yt_status.get(v_id)
            if not status:
                continue

            exists = status["exists"]
            valid = status["valid"]
            v_title = status["title"]
            cat_id = status["category_id"]

            # Safe ASCII versions for console output
            title_safe = title.encode('ascii', errors='replace').decode('ascii')
            v_title_safe = v_title.encode('ascii', errors='replace').decode('ascii')

            if not exists:
                print(f"[{i + 1}/{len(games)}] {title_safe} (id={game_id}) - Trailer ID {v_id} is DELETED/PRIVATE")
                deleted_count += 1
                invalidated_count += 1
                if not dry_run:
                    update_trailer(game_id, "", valid=False)
            elif not valid:
                print(f"[{i + 1}/{len(games)}] {title_safe} (id={game_id}) - Trailer ID {v_id} is NOT a game (Title: '{v_title_safe}', Category ID: {cat_id})")
                wrong_category_count += 1
                invalidated_count += 1
                if not dry_run:
                    update_trailer(game_id, "", valid=False)

        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print(f"  Total Checked       : {len(games)}")
        print(f"  Deleted/Private     : {deleted_count}")
        print(f"  Wrong Category      : {wrong_category_count}")
        print(f"  Total Invalidated   : {invalidated_count}")
        if dry_run:
            print(f"  (Dry Run mode: No database records were modified)")
        print("=" * 60)
        return

    print("=" * 60)
    print("TimeToBeat - Trailer Fetcher")
    print(f"Mode  : {'TEST (5 games)' if test_mode else 'FULL'}")
    if dry_run:
        print("Dry Run: Active (No database updates will be made)")
    print("=" * 60)

    if query_test:
        print(f"\n[QUERY TEST] Testing trailer search for: '{query_test}'")
        # Test IGDB
        video_id = get_trailer_from_igdb(query_test)
        if video_id:
            print(f"  IGDB Result: Found YouTube ID: {video_id} (URL: https://youtube.com/watch?v={video_id})")
        else:
            print("  IGDB Result: Not Found")
        
        # Test YouTube
        if YOUTUBE_API_KEY:
            try:
                yt_id = search_trailer(query_test)
                if yt_id:
                    print(f"  YouTube Result: Found YouTube ID: {yt_id} (URL: https://youtube.com/watch?v={yt_id})")
                else:
                    print("  YouTube Result: Not Found")
            except Exception as e:
                print(f"  YouTube Search Error: {e}")
        else:
            print("  YouTube Result: Skipped (API Key not configured)")
        return

    limit = 5 if test_mode else 1000
    games = get_games_without_trailer(limit=limit)

    print(f"\nGames in queue: {len(games)}")
    if not games:
        print("No games without trailers found. All done!")
        return

    # Check YouTube API credentials if we need to fall back
    if not YOUTUBE_API_KEY:
        print("\nWARNING: YOUTUBE_API_KEY not set in .env.")
        print("YouTube Search fallback will be unavailable.")
        print("We will only use IGDB for searching trailers.\n")

    updated = 0
    updated_via_igdb = 0
    updated_via_youtube = 0
    skipped_not_found = 0
    skipped_error = 0
    interrupted = False

    print()

    try:
        for i, game in enumerate(games):
            game_id = game["id"]
            title = game["title"]
            title_safe = title.encode('ascii', errors='replace').decode('ascii')

            print(f"[{i + 1}/{len(games)}] {title_safe} (id={game_id})")

            # 1. Try IGDB first (Free, 0 units)
            video_id = get_trailer_from_igdb(title)
            if video_id:
                if dry_run:
                    print(f"    [DRY RUN] Would update via IGDB - trailer_youtube_id={video_id}")
                    updated += 1
                    updated_via_igdb += 1
                else:
                    success = update_trailer(game_id, video_id, valid=True)
                    if success:
                        print(f"    [OK] UPDATED via IGDB - trailer_youtube_id={video_id}")
                        updated += 1
                        updated_via_igdb += 1
                    else:
                        print(f"    [ERROR] DB update failed")
                        skipped_error += 1
                continue

            # 2. Fallback to YouTube Search (100 units)
            if not YOUTUBE_API_KEY:
                # Mark as empty if YouTube is not configured and IGDB failed
                if dry_run:
                    print(f"    [DRY RUN] Would mark as NOT FOUND (IGDB failed & YouTube API Key not set)")
                    skipped_not_found += 1
                else:
                    success = update_trailer(game_id, "", valid=False)
                    if success:
                        print(f"    [SKIP] IGDB failed & YouTube API Key not set, marked as NOT FOUND")
                        skipped_not_found += 1
                    else:
                        print(f"    [ERROR] DB update failed")
                        skipped_error += 1
                continue

            time.sleep(REQUEST_DELAY)
            video_id = search_trailer(title)
            if video_id:
                if dry_run:
                    print(f"    [DRY RUN] Would update via YouTube - trailer_youtube_id={video_id}")
                    updated += 1
                    updated_via_youtube += 1
                else:
                    success = update_trailer(game_id, video_id, valid=True)
                    if success:
                        print(f"    [OK] UPDATED via YouTube - trailer_youtube_id={video_id}")
                        updated += 1
                        updated_via_youtube += 1
                    else:
                        print(f"    [ERROR] DB update failed")
                        skipped_error += 1
            else:
                # Mark as empty to avoid reprocessing in subsequent runs
                if dry_run:
                    print(f"    [DRY RUN] Would mark as NOT FOUND (YouTube search failed)")
                    skipped_not_found += 1
                else:
                    success = update_trailer(game_id, "", valid=False)
                    if success:
                        print(f"    [SKIP] no trailer found, marked as NOT FOUND")
                        skipped_not_found += 1
                    else:
                        print(f"    [ERROR] DB update failed")
                        skipped_error += 1

            time.sleep(REQUEST_DELAY)

    except QuotaExceededException:
        print("\n[ERROR] YouTube API quota limit reached!")
        interrupted = True
    except InvalidApiKeyException:
        print("\n[ERROR] Invalid YouTube API Key configuration!")
        interrupted = True
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        interrupted = True

    # Summary
    print("\n" + "=" * 60)
    print("RUN SUMMARY")
    print(f"  Total Updated     : {updated} (IGDB: {updated_via_igdb}, YouTube: {updated_via_youtube})")
    print(f"  Not found         : {skipped_not_found}")
    print(f"  DB Error          : {skipped_error}")
    print("=" * 60)

    # Quota calculations
    approx_units = updated_via_youtube * 100
    print(f"\nYouTube API units used in this session: ~{approx_units:,}")
    print(f"Daily quota limit: 10,000 units")
    if interrupted:
        print("\nYou can run the script again anytime. It will resume automatically where you left off.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Test mode: process 5 games (or 20 in validate mode)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run: perform searches but do not update database")
    parser.add_argument("--query", type=str, help="Directly test YouTube search for a specific game title")
    parser.add_argument("--validate", action="store_true", help="Validate existing trailers and reset invalid ones")
    args = parser.parse_args()

    run(test_mode=args.test, dry_run=args.dry_run, query_test=args.query, validate_mode=args.validate)