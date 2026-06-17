"""
settings.py  (SERVER SIDE ONLY)

Loads + validates the environment variables needed to FETCH trend data.
This module is imported only by generate_feed.py (and the instagram/tiktok
fetchers it uses), which runs in GitHub Actions — NOT on user machines.

The Claude skill side (prepare_digest.py, deliver.py) never imports this.
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


# ── Instagram (Meta Graph API) ───────────────────────────────
INSTAGRAM_ACCESS_TOKEN = _require("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_USER_ID = _require("INSTAGRAM_USER_ID")
INSTAGRAM_API_VERSION = _optional("INSTAGRAM_API_VERSION", "v21.0")
INSTAGRAM_BASE_URL = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}"

# Optional — only needed if you wire up app-level token refresh.
META_APP_ID = _optional("META_APP_ID")
META_APP_SECRET = _optional("META_APP_SECRET")

# ── TikTok (third-party) ─────────────────────────────────────
ENSEMBLEDATA_API_TOKEN = _optional("ENSEMBLEDATA_API_TOKEN")
LAMATOK_API_KEY = _optional("LAMATOK_API_KEY")

if not ENSEMBLEDATA_API_TOKEN and not LAMATOK_API_KEY:
    raise EnvironmentError(
        "Set at least one TikTok API key: ENSEMBLEDATA_API_TOKEN or LAMATOK_API_KEY"
    )

TIKTOK_PROVIDER = "ensembledata" if ENSEMBLEDATA_API_TOKEN else "lamatok"

# ── What to track ────────────────────────────────────────────
HASHTAGS_TO_TRACK = [
    h.strip().lstrip("#")
    for h in _optional("HASHTAGS_TO_TRACK", "skincare,aestheticfashion").split(",")
    if h.strip()
]
TIKTOK_REGIONS = [
    r.strip() for r in _optional("TIKTOK_REGIONS", "GB,US").split(",") if r.strip()
]
