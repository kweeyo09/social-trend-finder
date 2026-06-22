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

    errors, reels = [], []
    try:
        ranked = scorer.rank_instagram_reels(instagram.fetch_all_reels())
        for r in ranked:
            reels.append({
                "query": r.get("query"),
                "caption": r.get("caption"),
                "owner": r.get("owner"),
                "like_count": r.get("like_count", 0),
                "comments_count": r.get("comments_count", 0),
                "play_count": r.get("play_count", 0),
                "duration": r.get("duration", 0),
                "velocity": r.get("velocity", 0),
                "norm": r.get("norm", 0),
                "url": r.get("url"),
                "timestamp": r.get("timestamp"),
            })
    except Exception as e:
        logger.error(f"Instagram fetch failed: {e}")
        errors.append(str(e))
    return {"platform": "instagram", "generatedAt": _now(), "reels": reels, "errors": errors}


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
                "rank": h.get("rank", 0),
                "rank_diff": h.get("rank_diff", 0),
                "norm": h.get("norm", 0),
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


def build_reddit_feed() -> dict:
    import reddit
    import scorer

    errors, posts = [], []
    try:
        ranked = scorer.rank_reddit_posts(reddit.fetch_all_reddit_trends())
        for p in ranked:
            posts.append({
                "subreddit": p.get("subreddit"),
                "title": p.get("title"),
                "author": p.get("author"),
                "score": p.get("score", 0),
                "num_comments": p.get("num_comments", 0),
                "velocity": p.get("velocity", 0),
                "norm": p.get("norm", 0),
                "permalink": p.get("permalink"),
                "external_url": p.get("external_url"),
                "is_video": p.get("is_video", False),
                "timestamp": p.get("timestamp"),
            })
    except Exception as e:
        logger.error(f"Reddit fetch failed: {e}")
        errors.append(str(e))
    return {"platform": "reddit", "generatedAt": _now(), "posts": posts, "errors": errors}


def build_youtube_feed() -> dict:
    import youtube
    import scorer

    errors, shorts, long = [], [], []
    try:
        ranked = scorer.rank_youtube_videos(youtube.fetch_all_youtube_trends())

        def _shape(v):
            return {
                "title": v.get("title"),
                "channel": v.get("channel"),
                "url": v.get("url"),
                "views": v.get("views", 0),
                "likes": v.get("likes", 0),
                "comments": v.get("comments", 0),
                "duration": v.get("duration", 0),
                "velocity": v.get("velocity", 0),
                "norm": v.get("norm", 0),
                "timestamp": v.get("timestamp"),
            }

        shorts = [_shape(v) for v in ranked.get("shorts", [])]
        long = [_shape(v) for v in ranked.get("long", [])]
    except Exception as e:
        logger.error(f"YouTube fetch failed: {e}")
        errors.append(str(e))
    return {
        "platform": "youtube",
        "generatedAt": _now(),
        "shorts": shorts,
        "long": long,
        "errors": errors,
    }


def main():
    ap = argparse.ArgumentParser(description="Generate trend feeds for the Claude skill.")
    ap.add_argument("--instagram-only", action="store_true")
    ap.add_argument("--tiktok-only", action="store_true")
    ap.add_argument("--reddit-only", action="store_true")
    ap.add_argument("--youtube-only", action="store_true")
    args = ap.parse_args()

    # If any --x-only flag is set, run only those; otherwise run everything.
    only = {
        "instagram": args.instagram_only,
        "tiktok": args.tiktok_only,
        "reddit": args.reddit_only,
        "youtube": args.youtube_only,
    }
    run_all = not any(only.values())

    if run_all or only["instagram"]:
        feed = build_instagram_feed()
        (ROOT / "feed-instagram.json").write_text(json.dumps(feed, indent=2))
        logger.info(f"Wrote feed-instagram.json — {len(feed['reels'])} reels")

    if run_all or only["tiktok"]:
        feed = build_tiktok_feed()
        (ROOT / "feed-tiktok.json").write_text(json.dumps(feed, indent=2))
        logger.info(
            f"Wrote feed-tiktok.json — {len(feed['sounds'])} sounds, "
            f"{len(feed['hashtags'])} hashtags"
        )

    if run_all or only["reddit"]:
        feed = build_reddit_feed()
        (ROOT / "feed-reddit.json").write_text(json.dumps(feed, indent=2))
        logger.info(f"Wrote feed-reddit.json — {len(feed['posts'])} posts")

    if run_all or only["youtube"]:
        feed = build_youtube_feed()
        (ROOT / "feed-youtube.json").write_text(json.dumps(feed, indent=2))
        logger.info(
            f"Wrote feed-youtube.json — {len(feed['shorts'])} shorts, "
            f"{len(feed['long'])} long-form"
        )


if __name__ == "__main__":
    main()
