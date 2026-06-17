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


def score_instagram_post(post: dict) -> float:
    likes = post.get("like_count", 0)
    comments = post.get("comments_count", 0)
    timestamp = post.get("timestamp", "")
    hours = _hours_ago(timestamp)
    engagement = likes + (comments * 2)  # weight comments higher
    velocity = engagement / hours
    return round(velocity * _recency_weight(hours), 2)


def score_tiktok_sound(sound: dict) -> float:
    """Score a trending sound by video count growth signal."""
    # EnsembleData / LamaTok return different field names — handle both
    video_count = sound.get("video_count") or sound.get("videoCount", 0)
    # Sounds don't have timestamps in most APIs; rank by video count as proxy
    return float(video_count)


def rank_instagram_hashtags(hashtag_trends: list[dict]) -> list[dict]:
    """Score each hashtag's top posts and sort descending."""
    for ht in hashtag_trends:
        scores = [score_instagram_post(p) for p in ht.get("top_posts", [])]
        ht["avg_velocity"] = round(sum(scores) / len(scores), 2) if scores else 0
        ht["peak_velocity"] = max(scores, default=0)

    return sorted(hashtag_trends, key=lambda x: x["peak_velocity"], reverse=True)


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


def rank_tiktok_hashtags(hashtag_trends: list[dict]) -> list[dict]:
    """Sort TikTok hashtags by view count."""
    return sorted(hashtag_trends, key=lambda x: x.get("view_count", 0), reverse=True)
