"""
instagram.py  (SERVER SIDE — runs in GitHub Actions)

Fetches trending Instagram Reels via the ScrapeCreators API
(https://docs.scrapecreators.com/v2/instagram/reels/search). One search per
tracked term in HASHTAGS_TO_TRACK; results are normalised so the scorer can
rank them by engagement velocity.

This replaces the old Meta Graph integration — no Instagram access token,
user id, app secret, or 60-day token refresh needed anymore.
"""

import logging
import settings
from base_fetcher import safe_get

logger = logging.getLogger(__name__)

BASE = settings.SCRAPECREATORS_BASE
HEADERS = {"x-api-key": settings.SCRAPECREATORS_API_KEY}


def _normalise(reel: dict, query: str) -> dict:
    owner = reel.get("owner") or {}
    return {
        "platform": "instagram",
        "query": query,
        "shortcode": reel.get("shortcode") or reel.get("code", ""),
        "caption": (reel.get("caption") or "")[:280],
        "owner": owner.get("username", ""),
        "owner_verified": owner.get("is_verified", False),
        # Map to the field names the scorer expects.
        "like_count": reel.get("like_count", 0),
        "comments_count": reel.get("comment_count", 0),
        "play_count": reel.get("video_play_count") or reel.get("video_view_count", 0),
        "duration": reel.get("video_duration", 0),
        "timestamp": reel.get("taken_at", ""),
        "url": reel.get("url", ""),
    }


def search_reels(query: str) -> list[dict]:
    """Search Reels for one keyword/hashtag within the configured window."""
    data = safe_get(
        f"{BASE}/v2/instagram/reels/search",
        params={"query": query, "date_posted": settings.IG_DATE_POSTED},
        headers=HEADERS,
    )
    reels = data.get("reels", []) or data.get("items", []) or data.get("data", [])
    return [_normalise(r, query) for r in reels]


def fetch_all_reels() -> list[dict]:
    """Main entry point: search Reels for every tracked term, return them all."""
    out: list[dict] = []
    for tag in settings.HASHTAGS_TO_TRACK:
        logger.info(f"Searching Instagram Reels for: {tag}")
        try:
            out.extend(search_reels(tag))
        except Exception as e:
            logger.error(f"Failed Instagram reel search '{tag}': {e}")
    return out
