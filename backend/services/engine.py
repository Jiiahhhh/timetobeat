import json
from services.supabase_client import supabase
from core.constants import VIBE_TO_GENRES, DIFFICULTY_LABELS
from schemas.request_models import RecommendRequest

def parse_genres(genres_val):
    if isinstance(genres_val, list): return genres_val
    if isinstance(genres_val, str):
        try: return json.loads(genres_val)
        except: return [genres_val]
    return []

def parse_platforms(platforms_val):
    if isinstance(platforms_val, list): return platforms_val
    if isinstance(platforms_val, str):
        try: return json.loads(platforms_val)
        except: return [platforms_val]
    return []

def get_recommendations(req: RecommendRequest) -> dict:
    time_hours = req.time_available / 60
    target_genres = VIBE_TO_GENRES.get(req.vibe, VIBE_TO_GENRES["surprise"])

    res = supabase.table("games").select("*").execute()
    all_games = res.data

    # Normalize
    for g in all_games:
        g["genres"] = parse_genres(g["genres"])
        g["platforms"] = parse_platforms(g["platforms"])

    # Filter by genre
    filtered = [g for g in all_games if any(genre in g["genres"] for genre in target_genres)]

    # Filter by platform
    if req.platform and req.platform != "any":
        filtered = [g for g in filtered if req.platform in g["platforms"]]

    # available difficulties before modifier
    available_diffs = list(set([g.get("difficulty") or 3 for g in filtered]))

    # Apply modifier filters
    if req.modifier == "coop":
        coop_games = [g for g in all_games if g.get("is_coop")]
        if req.platform and req.platform != "any":
            platform_map = {"steam": "Steam", "gog": "GOG", "epic": "Epic"}
            plat = platform_map.get(req.platform)
            if plat:
                coop_games = [g for g in coop_games if plat in g["platforms"]]
        if len(coop_games) >= 1:
            filtered = coop_games

    elif req.modifier == "intensity" and req.max_difficulty:
        exact = [g for g in filtered if (g.get("difficulty") or 3) == req.max_difficulty]
        if len(exact) == 0:
            exact = [g for g in filtered if abs((g.get("difficulty") or 3) - req.max_difficulty) <= 1]
        if len(exact) >= 1:
            filtered = exact

    # Exclude titles
    if req.exclude_titles:
        filtered = [g for g in filtered if g["title"] not in req.exclude_titles]

    # Scoring Engine
    def score(g):
        rating = float(g["rating"] or 0)
        main_hours = float(g["hltb_main"] or 0)
        sessions_needed = main_hours / time_hours if time_hours > 0 else 999

        if sessions_needed <= 1: bonus = 20
        elif sessions_needed <= 3: bonus = 15
        elif sessions_needed <= 7: bonus = 10
        elif sessions_needed <= 14: bonus = 3
        elif sessions_needed <= 30: bonus = 0
        else: bonus = -30

        return rating + bonus

    # Sort & Deduplicate
    sorted_games = sorted(filtered, key=score, reverse=True)
    
    seen = set()
    unique = []
    for g in sorted_games:
        if g["title"] not in seen:
            seen.add(g["title"])
            unique.append(g)

    if not unique:
        unique = all_games 

    def format_game(g):
        main = float(g["hltb_main"] or 0)
        days = round(main / time_hours) if time_hours > 0 and main > 0 else None
        framing = f"~{main}h main story"
        if days and days <= 365:
            framing += f" — finish in ~{days} days at your pace"
        diff = g.get("difficulty") or 3
        return {
            "title": g["title"],
            "cover_url": g["cover_url"],
            "genres": g["genres"],
            "platforms": g["platforms"],
            "rating": float(g["rating"] or 0),
            "main_story": main,
            "main_extra": float(g["hltb_extra"] or 0),
            "difficulty": diff,
            "difficulty_label": DIFFICULTY_LABELS.get(diff, "⚔️ Fair fight"),
            "framing": framing,
            "steam_app_id": g.get("steam_app_id"),
            "trailer_youtube_id": g.get("trailer_youtube_id"),
            "short_description": g.get("short_description"),
            "trailer_valid": g.get("trailer_valid") or False,
        }

    primary = format_game(unique[0]) if len(unique) > 0 else None
    alts = [format_game(g) for g in unique[1:3]]

    return {
        "primary": primary,
        "alternatives": alts,
        "meta": {
            "time_available_minutes": req.time_available,
            "vibe": req.vibe,
            "platform": req.platform,
            "modifier": req.modifier,
            "total_matches": len(unique),
            "available_difficulties": available_diffs
        }
    }