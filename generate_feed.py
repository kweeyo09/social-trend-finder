#!/usr/bin/env python3
"""
generate_feed.py  (SERVER SIDE — runs in GitHub Actions, NOT on user machines)

Fetches Instagram + TikTok trends using the API keys stored as GitHub Secrets,
scores them by engagement velocity, and writes feed-instagram.json and
feed-tiktok.json to the repo root. A scheduled workflow commits these feeds so
the Claude skill can read them over plain HTTP with no keys of its own.

Run:  python generate_feed.py [--instagram-only | --tiktok-only]
"""

import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger("generate_feed")

ROOT = Path(__file__).resolve().parent


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_instagram_feed() -> dict:
    # Imported lazily so --help works without API keys configured.
    import instagram
    import scorer

    errors, hashtags = [], []
    try:
        ranked = scorer.rank_instagram_hashtags(instagram.fetch_all_hashtag_trends())
        for h in ranked:
            hashtags.append({
                "hashtag": h.get("hashtag"),
                "peak_velocity": h.get("peak_velocity", 0),
                "avg_velocity": h.get("avg_velocity", 0),
                "recent_count": h.get("recent_count", 0),
                "top_likes": h.get("top_likes", 0),
            })
    except Exception as e:
        logger.error(f"Instagram fetch failed: {e}")
        errors.append(str(e))
    return {"platform": "instagram", "generatedAt": _now(), "hashtags": hashtags, "errors": errors}


def build_tiktok_feed() -> dict:
    import tiktok
    import scorer

    errors, sounds, hashtags = [], [], []
    try:
        raw = tiktok.fetch_all_tiktok_trends()
        for s in scorer.rank_tiktok_sounds(raw.get("sounds", [])):
            sounds.append({
                "title": s.get("title") or s.get("music_title"),
                "author": s.get("author") or s.get("music_author"),
                "videos": int(s.get("score", 0)),
                "region": s.get("region", ""),
            })
        for h in scorer.rank_tiktok_hashtags(raw.get("hashtags", [])):
            hashtags.append({
                "hashtag": h.get("hashtag"),
                "view_count": h.get("view_count", 0),
                "video_count": h.get("video_count", 0),
            })
    except Exception as e:
        logger.error(f"TikTok fetch failed: {e}")
        errors.append(str(e))
    return {
        "platform": "tiktok",
        "generatedAt": _now(),
        "sounds": sounds,
        "hashtags": hashtags,
        "errors": errors,
    }


def main():
    ap = argparse.ArgumentParser(description="Generate trend feeds for the Claude skill.")
    ap.add_argument("--instagram-only", action="store_true")
    ap.add_argument("--tiktok-only", action="store_true")
    args = ap.parse_args()

    if not args.tiktok_only:
        feed = build_instagram_feed()
        (ROOT / "feed-instagram.json").write_text(json.dumps(feed, indent=2))
        logger.info(f"Wrote feed-instagram.json — {len(feed['hashtags'])} hashtags")

    if not args.instagram_only:
        feed = build_tiktok_feed()
        (ROOT / "feed-tiktok.json").write_text(json.dumps(feed, indent=2))
        logger.info(
            f"Wrote feed-tiktok.json — {len(feed['sounds'])} sounds, "
            f"{len(feed['hashtags'])} hashtags"
        )


if __name__ == "__main__":
    main()
