"""
tiktok.py
Fetches trending sounds, hashtags, and keyword data from TikTok
via EnsembleData (primary) or LamaTok (fallback).

NOTE: The official TikTok API does NOT expose trending sounds or
discovery data. This module uses third-party APIs. Verify your
provider's ToS for your use case.
"""

import logging
import settings
from base_fetcher import safe_get

logger = logging.getLogger(__name__)

PROVIDER = settings.TIKTOK_PROVIDER

# ── EnsembleData endpoints ───────────────────────────────────
ENSEMBLE_BASE = "https://ensembledata.com/apis/tt"
ENSEMBLE_TOKEN = settings.ENSEMBLEDATA_API_TOKEN

# ── LamaTok endpoints ────────────────────────────────────────
LAMATOK_BASE = "https://api.lamatok.com"
LAMATOK_KEY = settings.LAMATOK_API_KEY


# ── EnsembleData fetchers ────────────────────────────────────

def _ensemble_trending_sounds(region: str) -> list[dict]:
    data = safe_get(
        f"{ENSEMBLE_BASE}/music/trending",
        params={"token": ENSEMBLE_TOKEN, "region": region},
    )
    return data.get("data", {}).get("music_list", [])


def _ensemble_hashtag_search(hashtag: str) -> dict:
    data = safe_get(
        f"{ENSEMBLE_BASE}/hashtag/search",
        params={"token": ENSEMBLE_TOKEN, "name": hashtag},
    )
    return data.get("data", {})


def _ensemble_keyword_search(keyword: str, days: int = 7) -> list[dict]:
    data = safe_get(
        f"{ENSEMBLE_BASE}/keyword/search",
        params={"token": ENSEMBLE_TOKEN, "keyword": keyword, "period": days},
    )
    return data.get("data", {}).get("videos", [])


# ── LamaTok fetchers ─────────────────────────────────────────

def _lamatok_trending_sounds(region: str) -> list[dict]:
    data = safe_get(
        f"{LAMATOK_BASE}/v1/trending/sounds",
        headers={"Authorization": f"Bearer {LAMATOK_KEY}"},
        params={"region": region},
    )
    return data.get("data", [])


def _lamatok_hashtag_search(hashtag: str) -> dict:
    data = safe_get(
        f"{LAMATOK_BASE}/v1/hashtag/info",
        headers={"Authorization": f"Bearer {LAMATOK_KEY}"},
        params={"name": hashtag},
    )
    return data.get("data", {})


# ── Public interface ─────────────────────────────────────────

def fetch_trending_sounds() -> list[dict]:
    """Fetch trending sounds across all configured regions."""
    sounds = []
    for region in settings.TIKTOK_REGIONS:
        logger.info(f"Fetching TikTok trending sounds for region: {region}")
        try:
            if PROVIDER == "ensembledata":
                region_sounds = _ensemble_trending_sounds(region)
            else:
                region_sounds = _lamatok_trending_sounds(region)

            for s in region_sounds:
                s["region"] = region
            sounds.extend(region_sounds)
        except Exception as e:
            logger.error(f"Failed to fetch sounds for {region}: {e}")

    return sounds


def fetch_trending_hashtags() -> list[dict]:
    """Fetch hashtag performance for tracked tags."""
    results = []
    for tag in settings.HASHTAGS_TO_TRACK:
        logger.info(f"Fetching TikTok hashtag data for #{tag}")
        try:
            if PROVIDER == "ensembledata":
                data = _ensemble_hashtag_search(tag)
            else:
                data = _lamatok_hashtag_search(tag)

            results.append(
                {
                    "platform": "tiktok",
                    "hashtag": tag,
                    "view_count": data.get("view_count", 0),
                    "video_count": data.get("video_count", 0),
                    "raw": data,
                }
            )
        except Exception as e:
            logger.error(f"Failed to fetch TikTok hashtag #{tag}: {e}")

    return results


def fetch_all_tiktok_trends() -> dict:
    """
    Main entry point: fetch sounds + hashtags.
    Returns dict with 'sounds' and 'hashtags' keys.
    """
    return {
        "sounds": fetch_trending_sounds(),
        "hashtags": fetch_trending_hashtags(),
    }
