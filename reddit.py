"""
reddit.py  (SERVER SIDE — runs in GitHub Actions, NOT on user machines)

Fetches trending Reddit posts with NO API key, using Reddit's public .json
endpoints (the same JSON you get by appending `.json` to any reddit URL).

Approach borrowed from github.com/mvanhorn/last30days-skill (reddit_public.py):
  - hit www.reddit.com/r/{sub}/top.json and www.reddit.com/search.json
  - send a real browser User-Agent (Reddit blocks blank/default agents)
  - rely on base_fetcher.safe_get for 429/5xx retry + backoff

Config comes straight from env so this stays decoupled from the keyed
Instagram/TikTok settings — a missing Meta token can't break the Reddit feed.
"""

import os
import logging
from datetime import datetime, timezone

from base_fetcher import safe_get

logger = logging.getLogger(__name__)

BASE = "https://www.reddit.com"

# Reddit rejects requests with no/blank User-Agent. Use a realistic browser UA.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _csv_env(key: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(key, default).split(",") if x.strip()]


# Communities + keyword searches to track. Override via repo Variables.
SUBREDDITS_TO_TRACK = _csv_env(
    "REDDIT_SUBREDDITS", "SkincareAddiction,beauty,femalefashionadvice,malefashion"
)
REDDIT_QUERIES = _csv_env("REDDIT_QUERIES", "")  # optional free-text searches
REDDIT_PERIOD = os.getenv("REDDIT_PERIOD", "week")  # hour|day|week|month|year|all
REDDIT_LIMIT = int(os.getenv("REDDIT_LIMIT", "25"))


def _to_iso(created_utc) -> str:
    try:
        return datetime.fromtimestamp(float(created_utc), tz=timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _normalise(child: dict, source: str) -> dict:
    d = child.get("data", {})
    return {
        "platform": "reddit",
        "source": source,                       # e.g. "r/beauty" or 'q:"lip oil"'
        "subreddit": d.get("subreddit", ""),
        "title": d.get("title", ""),
        "author": d.get("author", ""),
        "score": d.get("score", 0),             # net upvotes
        "num_comments": d.get("num_comments", 0),
        "upvote_ratio": d.get("upvote_ratio", 0),
        "timestamp": _to_iso(d.get("created_utc")),
        "permalink": f"{BASE}{d.get('permalink', '')}",
        "external_url": d.get("url", ""),       # linked article/video, if any
        "is_video": bool(d.get("is_video")),
    }


def fetch_subreddit_top(sub: str) -> list[dict]:
    """Top posts of the period for one subreddit."""
    data = safe_get(
        f"{BASE}/r/{sub}/top.json",
        params={"t": REDDIT_PERIOD, "limit": REDDIT_LIMIT, "raw_json": 1},
        headers=HEADERS,
    )
    children = data.get("data", {}).get("children", [])
    return [_normalise(c, f"r/{sub}") for c in children]


def search_reddit(query: str) -> list[dict]:
    """Site-wide search for a keyword, ranked by top of the period."""
    data = safe_get(
        f"{BASE}/search.json",
        params={
            "q": query,
            "sort": "top",
            "t": REDDIT_PERIOD,
            "limit": REDDIT_LIMIT,
            "raw_json": 1,
        },
        headers=HEADERS,
    )
    children = data.get("data", {}).get("children", [])
    return [_normalise(c, f'q:"{query}"') for c in children]


def fetch_all_reddit_trends() -> list[dict]:
    """Main entry point: top posts across tracked subreddits + keyword searches."""
    posts: list[dict] = []

    for sub in SUBREDDITS_TO_TRACK:
        logger.info(f"Fetching Reddit top for r/{sub}")
        try:
            posts.extend(fetch_subreddit_top(sub))
        except Exception as e:
            logger.error(f"Failed r/{sub}: {e}")

    for q in REDDIT_QUERIES:
        logger.info(f"Searching Reddit for: {q}")
        try:
            posts.extend(search_reddit(q))
        except Exception as e:
            logger.error(f"Failed Reddit search '{q}': {e}")

    return posts
