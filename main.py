"""
main.py
Orchestrates the full trend-finder workflow:
  FETCH → SCORE → SUMMARISE → EMAIL → LOG

Run once:    python main.py --once
Start scheduler: python scheduler.py
"""

import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path

from instagram import fetch_all_hashtag_trends
from tiktok import fetch_all_tiktok_trends
from scorer import (
    rank_instagram_hashtags,
    rank_tiktok_sounds,
    rank_tiktok_hashtags,
)
from summariser import generate_insight
from renderer import render_digest
from sender import send_digest
import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def log_run(run_time: datetime, ig_data: list, tt_data: dict, email_sent: bool):
    """Append run metadata to the log file."""
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "run_time": run_time.isoformat(),
        "email_sent": email_sent,
        "ig_hashtags_fetched": len(ig_data),
        "tt_sounds_fetched": len(tt_data.get("sounds", [])),
        "tt_hashtags_fetched": len(tt_data.get("hashtags", [])),
    }

    history = []
    if log_path.exists():
        with open(log_path) as f:
            history = json.load(f)

    history.append(entry)

    with open(log_path, "w") as f:
        json.dump(history, f, indent=2)


def run_trend_report():
    run_time = datetime.now(timezone.utc)
    logger.info(f"=== Trend Finder run started at {run_time.isoformat()} ===")

    # ── 1. FETCH ──────────────────────────────────────────────
    logger.info("Fetching Instagram trends…")
    ig_raw = fetch_all_hashtag_trends()

    logger.info("Fetching TikTok trends…")
    tt_raw = fetch_all_tiktok_trends()

    # ── 2. SCORE ──────────────────────────────────────────────
    ig_ranked = rank_instagram_hashtags(ig_raw)
    tt_sounds_ranked = rank_tiktok_sounds(tt_raw.get("sounds", []))
    tt_hashtags_ranked = rank_tiktok_hashtags(tt_raw.get("hashtags", []))

    # ── 3. SUMMARISE ─────────────────────────────────────────
    logger.info("Generating Claude insights…")
    ig_insight = generate_insight(
        "Instagram",
        {"top_hashtags": [{"tag": h["hashtag"], "velocity": h["peak_velocity"]} for h in ig_ranked[:5]]},
    )
    tt_insight = generate_insight(
        "TikTok",
        {
            "top_sounds": [{"title": s.get("title"), "videos": s.get("score")} for s in tt_sounds_ranked[:5]],
            "top_hashtags": [{"tag": h["hashtag"], "views": h.get("view_count")} for h in tt_hashtags_ranked[:5]],
        },
    )

    # ── 4. EMAIL ─────────────────────────────────────────────
    logger.info("Rendering and sending digest email…")
    html = render_digest(
        ig_hashtags=ig_ranked,
        tt_sounds=tt_sounds_ranked,
        tt_hashtags=tt_hashtags_ranked,
        ig_insight=ig_insight,
        tt_insight=tt_insight,
        run_time=run_time,
    )

    subject = f"📈 Social Trends Digest — {run_time.strftime('%-d %b %Y')}"
    email_sent = send_digest(subject, html)

    # ── 5. LOG ───────────────────────────────────────────────
    log_run(run_time, ig_raw, tt_raw, email_sent)
    logger.info(f"=== Run complete. Email sent: {email_sent} ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.once:
        run_trend_report()
    else:
        print("Use 'python scheduler.py' to start the scheduled runner.")
        print("Use 'python main.py --once' for a one-off run.")
