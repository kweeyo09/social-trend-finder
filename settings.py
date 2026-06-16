"""
config/settings.py
Loads and validates all environment variables.
Raises clear errors at startup if required vars are missing.
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


# ── Instagram ────────────────────────────────────────────────
META_APP_ID = _require("META_APP_ID")
META_APP_SECRET = _require("META_APP_SECRET")
INSTAGRAM_ACCESS_TOKEN = _require("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_USER_ID = _require("INSTAGRAM_USER_ID")
INSTAGRAM_API_VERSION = _optional("INSTAGRAM_API_VERSION", "v21.0")
INSTAGRAM_BASE_URL = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}"

# ── TikTok (third-party) ─────────────────────────────────────
ENSEMBLEDATA_API_TOKEN = _optional("ENSEMBLEDATA_API_TOKEN")
LAMATOK_API_KEY = _optional("LAMATOK_API_KEY")

# Validate at least one TikTok provider is configured
if not ENSEMBLEDATA_API_TOKEN and not LAMATOK_API_KEY:
    raise EnvironmentError(
        "Set at least one TikTok API key: ENSEMBLEDATA_API_TOKEN or LAMATOK_API_KEY"
    )

TIKTOK_PROVIDER = "ensembledata" if ENSEMBLEDATA_API_TOKEN else "lamatok"

# ── Email ────────────────────────────────────────────────────
SENDGRID_API_KEY = _require("SENDGRID_API_KEY")
EMAIL_FROM = _require("EMAIL_FROM")
EMAIL_TO = [e.strip() for e in _require("EMAIL_TO").split(",")]

# ── Claude ───────────────────────────────────────────────────
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")

# ── Tracking config ──────────────────────────────────────────
HASHTAGS_TO_TRACK = [
    h.strip().lstrip("#")
    for h in _optional("HASHTAGS_TO_TRACK", "skincare,aestheticfashion").split(",")
]
TIKTOK_REGIONS = [
    r.strip() for r in _optional("TIKTOK_REGIONS", "GB,US").split(",")
]

# ── Scheduler ────────────────────────────────────────────────
TIMEZONE = _optional("TIMEZONE", "Europe/London")

# ── Logging ──────────────────────────────────────────────────
LOG_FILE = _optional("LOG_FILE", "data/trends_log.json")
