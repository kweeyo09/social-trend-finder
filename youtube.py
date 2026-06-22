"""
youtube.py  (SERVER SIDE — runs in GitHub Actions, NOT on user machines)

Fetches trending YouTube videos with NO API key, using yt-dlp's search +
metadata dump (same approach as github.com/mvanhorn/last30days-skill,
youtube_yt.py). yt-dlp is a binary installed via requirements.txt, so this
runs in the Action — never on a user's machine.

Each result carries `duration`, which we use to split SHORTS / reels (<= 60s)
from LONG-FORM video — the distinction the digest cares about.
"""

import os
import json
import shutil
import logging
import subprocess
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


def _csv_env(key: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(key, default).split(",") if x.strip()]


# Search queries to discover trending videos. Override via repo Variables.
YOUTUBE_QUERIES = _csv_env("YOUTUBE_QUERIES", "skincare routine,outfit ideas")
# How many videos yt-dlp pulls per query.
YOUTUBE_PER_QUERY = int(os.getenv("YOUTUBE_PER_QUERY", "12"))
# Only keep videos uploaded within this many days.
YOUTUBE_RECENT_DAYS = int(os.getenv("YOUTUBE_RECENT_DAYS", "30"))
SHORT_MAX_SECONDS = 60


def _yt_dlp_bin() -> str | None:
    return shutil.which("yt-dlp")


def _parse_upload_date(raw: str | None) -> str:
    # yt-dlp gives upload_date as "YYYYMMDD".
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.strptime(raw, "%Y%m%d").replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _search(query: str, count: int) -> list[dict]:
    """Run yt-dlp ytsearch and return one parsed JSON dict per video."""
    bin_ = _yt_dlp_bin()
    if not bin_:
        raise RuntimeError("yt-dlp not found on PATH (pip install yt-dlp)")

    cmd = [
        bin_,
        "--ignore-config",
        "--no-warnings",
        "--no-download",
        "--ignore-errors",
        "--dump-json",
        f"ytsearch{count}:{query}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    videos = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            videos.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not videos and proc.returncode != 0:
        logger.error(f"yt-dlp failed for '{query}': {proc.stderr[:200]}")
    return videos


def _normalise(v: dict, query: str) -> dict:
    duration = v.get("duration") or 0
    return {
        "platform": "youtube",
        "query": query,
        "video_id": v.get("id", ""),
        "title": v.get("title", ""),
        "channel": v.get("channel") or v.get("uploader", ""),
        "url": v.get("webpage_url") or f"https://youtu.be/{v.get('id', '')}",
        "views": v.get("view_count") or 0,
        "likes": v.get("like_count") or 0,
        "comments": v.get("comment_count") or 0,
        "duration": duration,
        "is_short": bool(duration) and duration <= SHORT_MAX_SECONDS,
        "timestamp": _parse_upload_date(v.get("upload_date")),
    }


def fetch_all_youtube_trends() -> list[dict]:
    """Main entry point: search each query, keep recent videos, normalise."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=YOUTUBE_RECENT_DAYS)
    out: list[dict] = []

    for q in YOUTUBE_QUERIES:
        logger.info(f"Searching YouTube for: {q}")
        try:
            raw = _search(q, YOUTUBE_PER_QUERY)
        except Exception as e:
            logger.error(f"YouTube search '{q}' failed: {e}")
            continue

        for v in raw:
            item = _normalise(v, q)
            try:
                fresh = datetime.fromisoformat(item["timestamp"]) >= cutoff
            except Exception:
                fresh = True
            if fresh:
                out.append(item)

    return out
