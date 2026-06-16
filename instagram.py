"""
src/fetchers/instagram.py
Fetches hashtag trend data from Meta Graph API.
"""

import logging
import requests
from config import settings
from src.fetchers.base_fetcher import safe_get

logger = logging.getLogger(__name__)

BASE = settings.INSTAGRAM_BASE_URL
TOKEN = settings.INSTAGRAM_ACCESS_TOKEN
USER_ID = settings.INSTAGRAM_USER_ID


def get_hashtag_id(hashtag: str) -> str | None:
    """Resolve a hashtag string to its IG node ID."""
    data = safe_get(
        f"{BASE}/ig_hashtag_search",
        params={"user_id": USER_ID, "q": hashtag, "access_token": TOKEN},
    )
    try:
        return data["data"][0]["id"]
    except (KeyError, IndexError):
        logger.warning(f"Hashtag not found: #{hashtag}")
        return None


def get_top_media(hashtag_id: str) -> list[dict]:
    """Get top posts for a hashtag node ID."""
    data = safe_get(
        f"{BASE}/{hashtag_id}/top_media",
        params={
            "fields": "id,media_type,like_count,comments_count,timestamp",
            "access_token": TOKEN,
        },
    )
    return data.get("data", [])


def get_recent_media(hashtag_id: str) -> list[dict]:
    """Get recent posts for a hashtag node ID."""
    data = safe_get(
        f"{BASE}/{hashtag_id}/recent_media",
        params={
            "fields": "id,media_type,like_count,comments_count,timestamp",
            "access_token": TOKEN,
        },
    )
    return data.get("data", [])


def get_account_reels() -> list[dict]:
    """
    Fetch recent Reels from the connected business account.
    Useful as a proxy for trending formats (own account only).
    Requires 1,000+ followers for insights.
    """
    data = safe_get(
        f"{BASE}/{USER_ID}/media",
        params={
            "fields": "id,media_type,like_count,comments_count,timestamp",
            "access_token": TOKEN,
        },
    )
    reels = [p for p in data.get("data", []) if p.get("media_type") == "REELS"]
    return reels


def refresh_token(current_token: str) -> str:
    """
    Refresh an Instagram long-lived token before 60-day expiry.
    Call this weekly via scheduler.
    """
    resp = requests.get(
        "https://graph.facebook.com/oauth/access_token",
        params={"grant_type": "ig_refresh_token", "access_token": current_token},
        timeout=10,
    )
    resp.raise_for_status()
    new_token = resp.json().get("access_token")
    logger.info("Instagram token refreshed successfully.")
    return new_token


def fetch_all_hashtag_trends() -> list[dict]:
    """
    Main entry point: fetch top + recent media for all tracked hashtags.
    Returns a list of hashtag trend dicts.
    """
    results = []
    for tag in settings.HASHTAGS_TO_TRACK:
        logger.info(f"Fetching Instagram trends for #{tag}")
        hashtag_id = get_hashtag_id(tag)
        if not hashtag_id:
            continue

        top = get_top_media(hashtag_id)
        recent = get_recent_media(hashtag_id)

        results.append(
            {
                "platform": "instagram",
                "hashtag": tag,
                "top_posts": top,
                "recent_posts": recent,
                "top_likes": max((p.get("like_count", 0) for p in top), default=0),
                "recent_count": len(recent),
            }
        )

    return results
