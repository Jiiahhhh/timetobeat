import json
import random
from services.supabase_client import supabase
from core.constants import VIBE_TO_GENRES, DIFFICULTY_LABELS
from schemas.request_models import RecommendRequest


def parse_genres(genres_val):
    """
    Parse the genres field from database into a list of strings.
    Handles JSON list inputs, JSON strings, and raw strings.
    """
    if isinstance(genres_val, list): return genres_val
    if isinstance(genres_val, str):
        try: return json.loads(genres_val)
        except: return [genres_val]
    return []


def parse_platforms(platforms_val):
    """
    Parse the platforms field from database into a list of strings.
    Handles JSON list inputs, JSON strings, and raw strings.
    """
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
    """
    Generate game recommendations based on the user's available time, vibe, platform, and other modifiers.
    Calculates custom suitability scores for games and returns a primary recommendation and alternatives.
    """
    time_hours = req.time_available / 60
    vibes = req.vibe if isinstance(req.vibe, list) else [req.vibe]
    
    target_genres = []
    for v in vibes:
        target_genres.extend(VIBE_TO_GENRES.get(v, []))
    target_genres = list(set(target_genres))

    query = supabase.table("games").select("*")

    is_surprise = "surprise" in vibes
    if not is_surprise and target_genres:
        query = query.overlaps("genres", target_genres)

    if req.platform and req.platform != "any":
        query = query.overlaps("platforms", [req.platform])

    res = query.execute()
    filtered = res.data

    for g in filtered:
        g["genres"] = parse_genres(g["genres"])
        g["platforms"] = parse_platforms(g["platforms"])

    if not filtered:
        return {
            "primary": None,
            "alternatives": [],
            "meta": {
                "time_available_minutes": req.time_available,
                "vibe": vibes,
                "platform": req.platform,
                "modifier": req.modifier,
                "total_matches": 0,
                "available_difficulties": [],
            }
        }

    all_games = filtered[:]

    available_diffs = list(set([g.get("difficulty") or 3 for g in filtered]))

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

    if req.exclude_titles:
        filtered = [g for g in filtered if g["title"] not in req.exclude_titles]

    def score(g):
        """
        Calculate game recommendation compatibility score based on rating, session fit,
        completion ratio, and genre matches. Applies surprise-mode underdog boosts.
        """
        if "relaxed" in vibes:
            diff = g.get("difficulty") or 3
            if diff >= 3:
                return -999

        rating = float(g["rating"] or 70)

        main_hours = float(g["hltb_main"] or 0)
        sessions = main_hours / time_hours if time_hours > 0 else 999

        if sessions <= 1:    fit_bonus = 25
        elif sessions <= 3:  fit_bonus = 20
        elif sessions <= 7:  fit_bonus = 15
        elif sessions <= 14: fit_bonus = 8
        elif sessions <= 30: fit_bonus = 2
        else:                fit_bonus = -20

        sweet_spot = 5 if 2 <= sessions <= 5 else 0

        comp = float(g["hltb_completionist"] or 0)
        main = float(g["hltb_main"] or 0)
        completion_bonus = 0
        if comp > 0 and main > 0:
            ratio = comp / main
            if ratio <= 2:    completion_bonus = 5
            elif ratio <= 4:  completion_bonus = 2
            else:             completion_bonus = -3

        if not is_surprise:
            game_genres = g.get("genres", [])
            matched = sum(1 for genre in target_genres if genre in game_genres)
            if matched == len(vibes):
                genre_bonus = 15
            elif matched >= 2:
                genre_bonus = 8
            elif matched == 1:
                genre_bonus = 0
            else:
                genre_bonus = -10
        else:
            genre_bonus = 0  
            
        if is_surprise:
            if 75 <= rating <= 85:
                underdog_bonus = random.randint(10, 25)
            else:
                underdog_bonus = 0
        else:
            underdog_bonus = 0

        return rating + fit_bonus + sweet_spot + completion_bonus + genre_bonus + underdog_bonus

    sorted_games = sorted(filtered, key=score, reverse=True)

    shuffled_games = tier_shuffle(sorted_games, tier_size=5)

    seen = set()
    unique = []
    for g in shuffled_games:
        if g["title"] not in seen:
            seen.add(g["title"])
            unique.append(g)

    if not unique:
        unique = all_games

    def format_game(g):
        """
        Format internal game database object into client-safe representation,
        calculating session progress and generating localized flavor explanation text.
        """
        main = float(g["hltb_main"] or 0)
        days = round(main / time_hours) if time_hours > 0 and main > 0 else None
        framing = f"~{main}h main story"
        if days and days <= 365:
            framing += f" — finish in ~{days} days at your pace"
        diff = g.get("difficulty") or 3
        game_genres = g.get("genres", [])

        sessions = main / time_hours if time_hours > 0 and main > 0 else 999

        if req.modifier == "coop":
            if sessions <= 1:
                explanation = "A great co-op game for tonight"
            else:
                explanation = "A co-op game you can finish together"
        elif sessions <= 1:
            explanation = "You can finish this tonight"
        elif sessions <= 3:
            explanation = "Completable in a few sessions"
        elif sessions <= 7:
            explanation = "Great for this week"
        elif sessions <= 14:
            explanation = "A solid 2-week game"
        else:
            explanation = "A longer commitment, but worth it"

        vibe_explanations = {
            "relaxed": "Perfect for winding down",
            "story":   "A story worth experiencing",
            "action":  "High-intensity from start to finish",
            "rpg":     "Deep enough to get lost in",
            "puzzle":  "Satisfying to think through",
        }

        primary_vibe = vibes[0] if vibes else None
        if primary_vibe:
            if primary_vibe == "surprise":
                game_genres = g.get("genres", [])
                if "Relaxed" in game_genres:
                    surprise_label = "Unexpectedly cozy"
                elif "Story" in game_genres:
                    surprise_label = "A hidden narrative gem"
                elif "Action" in game_genres:
                    surprise_label = "A wild card pick"
                elif "Puzzle" in game_genres:
                    surprise_label = "A puzzle you won't see coming"
                elif "RPG" in game_genres:
                    surprise_label = "An RPG you probably overlooked"
                elif "Classic" in game_genres:
                    surprise_label = "A retro surprise"
                else:
                    surprise_label = "Something you didn't know you needed"
                explanation += f" · {surprise_label}"
            elif primary_vibe in vibe_explanations:
                explanation += f" · {vibe_explanations[primary_vibe]}"

        return {
            "id": g["id"],
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
            "explanation": explanation,
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
            "vibe": req.vibe if isinstance(req.vibe, list) else [req.vibe],
            "platform": req.platform,
            "modifier": req.modifier,
            "total_matches": len(unique),
            "available_difficulties": available_diffs,
        }
    }
