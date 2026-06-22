"""
settings.py  (SERVER SIDE ONLY)

Loads + validates the environment variables needed to FETCH trend data.
Imported only by generate_feed.py and the keyed fetchers (instagram.py,
tiktok.py), which run in GitHub Actions — NOT on user machines.

The Claude skill side (prepare_digest.py, deliver.py) never imports this.

Keyed sources (TikTok + Instagram) now run through a SINGLE provider,
ScrapeCreators (https://scrapecreators.com), so only one paid key is needed.
YouTube (yt-dlp) and Reddit (public JSON) are keyless and read their own
config straight from env — they do not import this module.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing required env var: {key}")
    return val


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# ── ScrapeCreators (covers BOTH TikTok and Instagram) ────────
# One key, sent as the `x-api-key` header on every request.
SCRAPECREATORS_API_KEY = _require("SCRAPECREATORS_API_KEY")
SCRAPECREATORS_BASE = "https://api.scrapecreators.com"

# ── What to track ────────────────────────────────────────────
# Used as Instagram reel-search queries (one search per term).
HASHTAGS_TO_TRACK = [
    h.strip().lstrip("#")
    for h in _optional("HASHTAGS_TO_TRACK", "skincare,aestheticfashion").split(",")
    if h.strip()
]

# ── TikTok popular-hashtags options ──────────────────────────
# Country codes for the popular-hashtags endpoint (one call per country).
TIKTOK_COUNTRIES = [
    c.strip() for c in _optional("TIKTOK_COUNTRIES", "GB,US").split(",") if c.strip()
]
# Time window in days: 7, 30, or 120.
TIKTOK_PERIOD = int(_optional("TIKTOK_PERIOD", "7"))
# Optional industry filter, e.g. "beauty-and-personal-care" or
# "apparel-and-accessories". Blank = all industries.
TIKTOK_INDUSTRY = _optional("TIKTOK_INDUSTRY", "")

# ── Instagram reel-search options ────────────────────────────
# How far back to look: last-hour | last-day | last-week | last-month | last-year
IG_DATE_POSTED = _optional("IG_DATE_POSTED", "last-month")
