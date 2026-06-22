"""
tiktok.py  (SERVER SIDE — runs in GitHub Actions)

Fetches TikTok trends via the ScrapeCreators API
(https://scrapecreators.com). Replaces the old EnsembleData / LamaTok
integration — one ScrapeCreators key now covers both TikTok and Instagram.

Two signals:
  - Popular hashtags  — /v1/tiktok/hashtags/popular  (fully documented)
  - Trending sounds   — best-effort from /v1/tiktok/videos/popular

NOTE on sounds: ScrapeCreators' popular-videos response schema is not published
in the public docs index, so the music object is read DEFENSIVELY (several
candidate field names, never crashes). If the shape differs, sounds simply come
back empty and the hashtags signal still works.
"""

import logging
import settings
from base_fetcher import safe_get

logger = logging.getLogger(__name__)

BASE = settings.SCRAPECREATORS_BASE
HEADERS = {"x-api-key": settings.SCRAPECREATORS_API_KEY}


# ── Popular hashtags (documented endpoint) ───────────────────

def _popular_hashtags_for_country(country: str) -> list[dict]:
    params = {"period": settings.TIKTOK_PERIOD, "countryCode": country}
    if settings.TIKTOK_INDUSTRY:
        params["industry"] = settings.TIKTOK_INDUSTRY

    data = safe_get(f"{BASE}/v1/tiktok/hashtags/popular", params=params, headers=HEADERS)
    out = []
    for h in data.get("list", []):
        out.append({
            "platform": "tiktok",
            "hashtag": h.get("hashtag_name", ""),
            "view_count": h.get("video_views", 0),
            "video_count": h.get("publish_cnt", 0),
            "rank": h.get("rank", 0),
            "rank_diff": h.get("rank_diff", 0),
            "country": country,
        })
    return out


def fetch_trending_hashtags() -> list[dict]:
    """Popular hashtags across all configured countries."""
    results = []
    for country in settings.TIKTOK_COUNTRIES:
        logger.info(f"Fetching TikTok popular hashtags for {country}")
        try:
            results.extend(_popular_hashtags_for_country(country))
        except Exception as e:
            logger.error(f"Failed TikTok popular hashtags for {country}: {e}")
    return results


# ── Trending sounds (best-effort) ────────────────────────────

def _extract_music(video: dict) -> dict | None:
    """Pull a sound object out of a popular-video record, tolerating field drift."""
    music = (
        video.get("music")
        or video.get("music_info")
        or video.get("added_sound_music_info")
        or {}
    )
    if not isinstance(music, dict) or not music:
        return None
    title = music.get("title") or music.get("music_title") or music.get("song_name")
    if not title:
        return None
    return {
        "id": music.get("id") or music.get("music_id") or title,
        "title": title,
        "author": music.get("author") or music.get("author_name") or music.get("artist", ""),
        "video_count": music.get("user_count") or music.get("video_count", 0),
    }


def fetch_trending_sounds() -> list[dict]:
    """Best-effort: derive trending sounds from the popular-videos feed."""
    sounds = []
    for country in settings.TIKTOK_COUNTRIES:
        logger.info(f"Fetching TikTok popular videos (for sounds) — {country}")
        params = {"period": settings.TIKTOK_PERIOD, "countryCode": country}
        if settings.TIKTOK_INDUSTRY:
            params["industry"] = settings.TIKTOK_INDUSTRY
        try:
            data = safe_get(f"{BASE}/v1/tiktok/videos/popular", params=params, headers=HEADERS)
        except Exception as e:
            logger.error(f"Failed TikTok popular videos for {country}: {e}")
            continue

        videos = data.get("list") or data.get("videos") or data.get("data") or []
        for v in videos:
            music = _extract_music(v if isinstance(v, dict) else {})
            if music:
                music["region"] = country
                sounds.append(music)
    return sounds


# ── Public interface ─────────────────────────────────────────

def fetch_all_tiktok_trends() -> dict:
    """Main entry point: hashtags (primary) + sounds (best-effort)."""
    return {
        "sounds": fetch_trending_sounds(),
        "hashtags": fetch_trending_hashtags(),
    }
