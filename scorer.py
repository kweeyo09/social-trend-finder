"""
scorer.py
Scores trends by engagement velocity, not just raw numbers.
Surfaces what's accelerating NOW, not what's old and popular.
"""

from datetime import datetime, timezone


def _hours_ago(timestamp_str: str) -> float:
    """Parse ISO timestamp and return hours since now."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        hours = delta.total_seconds() / 3600
        return max(hours, 0.1)  # avoid division by zero
    except Exception:
        return 24.0  # default if unparseable


def _recency_weight(hours: float) -> float:
    """
    Decay weight: 1.0 at 0h → 0.1 at 48h.
    Posts older than 48h are deprioritised.
    """
    return max(0.1, 1 - (hours / 48))


def score_instagram_reel(reel: dict) -> float:
    """Velocity for a Reel: weighted engagement per hour, recency-decayed."""
    likes = reel.get("like_count", 0)
    comments = reel.get("comments_count", 0)
    hours = _hours_ago(reel.get("timestamp", ""))
    engagement = likes + (comments * 3)  # weight comments higher
    velocity = engagement / hours
    return round(velocity * _recency_weight(hours), 2)


def score_tiktok_sound(sound: dict) -> float:
    """Score a trending sound by video count growth signal."""
    # Field name varies by source — handle the common variants defensively.
    video_count = sound.get("video_count") or sound.get("videoCount", 0)
    # Sounds rarely carry timestamps; rank by video count as a popularity proxy.
    return float(video_count)


def rank_instagram_reels(reels: list[dict], author_cap: int = 2, top_n: int = 10) -> list[dict]:
    """Score reels by velocity, cap per owner, normalise, return top N."""
    for r in reels:
        r["velocity"] = score_instagram_reel(r)
    ranked = sorted(reels, key=lambda x: x["velocity"], reverse=True)
    ranked = _cap_per_author(ranked, "owner", author_cap)[:top_n]
    return _add_normalised(ranked, "velocity")


def rank_tiktok_sounds(sounds: list[dict]) -> list[dict]:
    """Deduplicate sounds across regions and rank by video count."""
    seen = set()
    unique = []
    for s in sounds:
        sound_id = s.get("id") or s.get("music_id") or s.get("title", "")
        if sound_id not in seen:
            seen.add(sound_id)
            s["score"] = score_tiktok_sound(s)
            unique.append(s)

    return sorted(unique, key=lambda x: x["score"], reverse=True)[:10]


def rank_tiktok_hashtags(hashtag_trends: list[dict], top_n: int = 15) -> list[dict]:
    """
    Deduplicate hashtags across countries (keep the highest view_count seen),
    sort by views, normalise to 0-100, and return the top N.
    """
    best: dict[str, dict] = {}
    for h in hashtag_trends:
        name = h.get("hashtag", "")
        if name not in best or h.get("view_count", 0) > best[name].get("view_count", 0):
            best[name] = h
    ranked = sorted(best.values(), key=lambda x: x.get("view_count", 0), reverse=True)[:top_n]
    return _add_normalised(ranked, "view_count")


# ── Reddit ───────────────────────────────────────────────────

def score_reddit_post(post: dict) -> float:
    """Velocity for a Reddit post: weighted engagement per hour, recency-decayed."""
    upvotes = post.get("score", 0)
    comments = post.get("num_comments", 0)
    hours = _hours_ago(post.get("timestamp", ""))
    engagement = upvotes + (comments * 3)  # comments are a stronger signal
    velocity = engagement / hours
    return round(velocity * _recency_weight(hours), 2)


def rank_reddit_posts(posts: list[dict], author_cap: int = 3, top_n: int = 15) -> list[dict]:
    """Score, sort by velocity, cap per author, normalise, return top N."""
    for p in posts:
        p["velocity"] = score_reddit_post(p)
    ranked = sorted(posts, key=lambda x: x["velocity"], reverse=True)
    ranked = _cap_per_author(ranked, "author", author_cap)[:top_n]
    return _add_normalised(ranked, "velocity")


# ── YouTube ──────────────────────────────────────────────────

def score_youtube_video(video: dict) -> float:
    """Velocity for a video: weighted engagement per hour since upload, decayed."""
    views = video.get("views", 0)
    likes = video.get("likes", 0)
    comments = video.get("comments", 0)
    hours = _hours_ago(video.get("timestamp", ""))
    engagement = views + (likes * 3) + (comments * 5)
    velocity = engagement / hours
    return round(velocity * _recency_weight(hours), 2)


def rank_youtube_videos(videos: list[dict], author_cap: int = 2, top_n: int = 10) -> dict:
    """
    Score every video, then split SHORTS (<=60s) from LONG-FORM, ranking and
    capping each list independently. Returns {"shorts": [...], "long": [...]}.
    """
    for v in videos:
        v["velocity"] = score_youtube_video(v)

    def _rank(items: list[dict]) -> list[dict]:
        ranked = sorted(items, key=lambda x: x["velocity"], reverse=True)
        ranked = _cap_per_author(ranked, "channel", author_cap)[:top_n]
        return _add_normalised(ranked, "velocity")

    return {
        "shorts": _rank([v for v in videos if v.get("is_short")]),
        "long": _rank([v for v in videos if not v.get("is_short")]),
    }


# ── Shared ranking helpers ───────────────────────────────────

def _cap_per_author(items: list[dict], author_key: str, cap: int) -> list[dict]:
    """Keep at most `cap` items per author so one voice can't dominate the digest."""
    seen: dict[str, int] = {}
    kept = []
    for item in items:
        author = item.get(author_key) or "_unknown"
        if seen.get(author, 0) >= cap:
            continue
        seen[author] = seen.get(author, 0) + 1
        kept.append(item)
    return kept


def _add_normalised(items: list[dict], src_key: str, dst_key: str = "norm") -> list[dict]:
    """
    Add a 0-100 `norm` score (min-max over this list) so items can be compared
    ACROSS platforms — a Reddit upvote and a TikTok view aren't comparable raw,
    but "how big is this for its own platform" is.
    """
    if not items:
        return items
    values = [i.get(src_key, 0) for i in items]
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    for i in items:
        i[dst_key] = round(((i.get(src_key, 0) - lo) / span) * 100, 1)
    return items
