import json
import random
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


def tier_shuffle(games: list, tier_size: int = 5) -> list:
    """
    Shuffle games within tiers of tier_size.
    Games in the same tier (similar score range) are randomized,
    but higher-scoring tiers always come before lower-scoring tiers.
    This ensures variety without sacrificing quality.
    """
    result = []
    for i in range(0, len(games), tier_size):
        tier = games[i:i + tier_size]
        random.shuffle(tier)
        result.extend(tier)
    return result


def get_recommendations(req: RecommendRequest) -> dict:
    time_hours = req.time_available / 60
    target_genres = VIBE_TO_GENRES.get(req.vibe, VIBE_TO_GENRES["surprise"])

    # ── Database-level filtering ────────────────────────────────────
    query = supabase.table("games").select("*")

    # Apply genre filter at database level (skip if surprise)
    if req.vibe != "surprise":
        query = query.overlaps("genres", target_genres)

    # Apply platform filter at database level
    if req.platform and req.platform != "any":
        query = query.overlaps("platforms", [req.platform])

    res = query.execute()
    filtered = res.data

    # ── Normalize data ──────────────────────────────────────────────
    for g in filtered:
        g["genres"] = parse_genres(g["genres"])
        g["platforms"] = parse_platforms(g["platforms"])

    # Store all_games for fallback
    all_games = filtered[:]

    # ── Available difficulties (before modifier) ───────────────────
    available_diffs = list(set([g.get("difficulty") or 3 for g in filtered]))

    # ── Modifier filters ────────────────────────────────────────────
    if req.modifier == "coop":
        coop_games = [g for g in filtered if g.get("is_coop")]

        if req.platform and req.platform != "any":
            platform_map = {
                "windows": "Windows",
                "mac": "Mac",
                "linux": "Linux",
                "steam deck": "Steam Deck",
            }
            plat = platform_map.get(req.platform.lower())
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

    # ── Exclude already-shown titles ────────────────────────────────
    if req.exclude_titles:
        filtered = [g for g in filtered if g["title"] not in req.exclude_titles]

    # ── Scoring Engine ──────────────────────────────────────────────
    def score(g):
        # 1. RATING — null = 70 (neutral, not 0)
        rating = float(g["rating"] or 70)

        # 2. SESSION FIT — how well game duration matches user time
        main_hours = float(g["hltb_main"] or 0)
        sessions = main_hours / time_hours if time_hours > 0 else 999

        if sessions <= 1:    fit_bonus = 25   # finish today
        elif sessions <= 3:  fit_bonus = 20   # finish in 3 days
        elif sessions <= 7:  fit_bonus = 15   # finish in a week
        elif sessions <= 14: fit_bonus = 8    # finish in 2 weeks
        elif sessions <= 30: fit_bonus = 2    # finish in a month
        else:                fit_bonus = -20  # too long

        # 3. SWEET SPOT BONUS — 2-5 sessions is ideal
        # Gives a sense of progress without being overwhelming
        sweet_spot = 5 if 2 <= sessions <= 5 else 0

        # 4. COMPLETION RATIO — proxy for gameplay quality
        # Games where completionist time is close to main story = engaging until the end
        comp = float(g["hltb_completionist"] or 0)
        main = float(g["hltb_main"] or 0)
        completion_bonus = 0
        if comp > 0 and main > 0:
            ratio = comp / main
            if ratio <= 2:    completion_bonus = 5   # close completionist time = engaging
            elif ratio <= 4:  completion_bonus = 2
            else:             completion_bonus = -3  # far completionist time = grindy

        return rating + fit_bonus + sweet_spot + completion_bonus

    # ── Sort + Tier Shuffle ────────────────────────────────────────
    sorted_games = sorted(filtered, key=score, reverse=True)

    # Shuffle within tiers — adds variety without sacrificing quality
    shuffled_games = tier_shuffle(sorted_games, tier_size=5)

    # ── Deduplicate ────────────────────────────────────────────────
    seen = set()
    unique = []
    for g in shuffled_games:
        if g["title"] not in seen:
            seen.add(g["title"])
            unique.append(g)

    # Fallback if filtered results are empty
    if not unique:
        unique = all_games

    # ── Format response ────────────────────────────────────────────
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
            "cover_portrait_url": g.get("cover_portrait_url"),
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
            "available_difficulties": available_diffs,
        }
    }