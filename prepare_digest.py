#!/usr/bin/env python3
"""
prepare_digest.py  (SKILL SIDE — runs inside Claude, NO API keys, stdlib only)

Gathers everything Claude needs to write the digest:
  - the central trend feeds (fetched over plain HTTP from the repo)
  - the prompt files that tell Claude how to summarise
  - the user's delivery config

Prints ONE JSON blob to stdout. Claude reads it, writes the email, then calls
deliver.py. No third-party packages required.

Run:  python3 prepare_digest.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request

SKILL_DIR = Path(__file__).resolve().parent
USER_DIR = Path.home() / ".social-trend-finder"
CONFIG_PATH = USER_DIR / "config.json"

# Where the central feeds live. Override with STF_FEED_BASE if you fork the repo.
FEED_BASE = os.environ.get(
    "STF_FEED_BASE",
    "https://raw.githubusercontent.com/kweeyo09/social-trend-finder/main",
)

PROMPT_FILES = ["digest-intro.md", "summarize-instagram.md", "summarize-tiktok.md"]

DEFAULT_CONFIG = {
    "recipients": [],
    "fromEmail": "",
    "frequency": "weekly",
    "language": "en",
}


def fetch_json(url: str):
    try:
        req = Request(url, headers={"User-Agent": "social-trend-finder"})
        with urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"_error": f"{e}"}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_PATH.read_text())}
        except Exception as e:
            return {**DEFAULT_CONFIG, "_configError": str(e)}
    return dict(DEFAULT_CONFIG)


def load_prompts() -> dict:
    # Priority: user override (~/.social-trend-finder/prompts) > shipped prompts.
    prompts = {}
    user_dir = USER_DIR / "prompts"
    local_dir = SKILL_DIR / "prompts"
    for fname in PROMPT_FILES:
        key = fname.replace(".md", "").replace("-", "_")
        up, lp = user_dir / fname, local_dir / fname
        if up.exists():
            prompts[key] = up.read_text()
        elif lp.exists():
            prompts[key] = lp.read_text()
    return prompts


def main():
    errors = []
    config = load_config()

    ig = fetch_json(f"{FEED_BASE}/feed-instagram.json")
    tt = fetch_json(f"{FEED_BASE}/feed-tiktok.json")

    if ig.get("_error"):
        errors.append(f"Could not fetch Instagram feed: {ig['_error']}")
        ig = {}
    if tt.get("_error"):
        errors.append(f"Could not fetch TikTok feed: {tt['_error']}")
        tt = {}
    for label, feed in (("Instagram", ig), ("TikTok", tt)):
        for note in (feed.get("errors") or []):
            errors.append(f"{label} feed note: {note}")

    prompts = load_prompts()
    if not prompts:
        errors.append("No prompt files found next to the skill.")

    out = {
        "status": "ok",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "config": {
            "recipients": config.get("recipients", []),
            "fromEmail": config.get("fromEmail", ""),
            "frequency": config.get("frequency", "weekly"),
            "language": config.get("language", "en"),
        },
        "instagram": {
            "hashtags": ig.get("hashtags", []),
            "feedGeneratedAt": ig.get("generatedAt"),
        },
        "tiktok": {
            "sounds": tt.get("sounds", []),
            "hashtags": tt.get("hashtags", []),
            "feedGeneratedAt": tt.get("generatedAt"),
        },
        "prompts": prompts,
        "stats": {
            "igHashtags": len(ig.get("hashtags", [])),
            "ttSounds": len(tt.get("sounds", [])),
            "ttHashtags": len(tt.get("hashtags", [])),
        },
        "errors": errors or None,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
