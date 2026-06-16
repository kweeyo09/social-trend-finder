---
name: social-trend-finder
description: >
  Monitors Instagram and TikTok for trending hashtags, sounds/audio, content
  formats, and engagement spikes. Runs on a schedule and delivers a digest
  email. Trigger this skill when asked to: check trends, run trend report,
  find trending sounds, monitor hashtags, send trend digest, or any variant
  of social listening for Instagram/TikTok.
---

# Social Trend Finder — Skill

## Purpose
Pull trending signals from Instagram (via Meta Graph API) and TikTok
(via EnsembleData or LamaTok third-party API) on a scheduled cadence,
score and rank them, then deliver a formatted digest email via SendGrid.

---

## Skill Workflow

```
1. FETCH     → Pull raw trend data from Instagram & TikTok APIs
2. SCORE     → Rank by engagement velocity (not just raw numbers)
3. SUMMARISE → Claude generates a brief narrative insight per trend
4. EMAIL     → Render HTML digest and send via SendGrid
5. LOG       → Append run metadata to trends_log.json
```

---

## Data Sources & Access Reality

### ⚠️ Critical API Notes (verified June 2026)

**Instagram (Meta Graph API)**
- **Free** — requires Facebook Developer account + OAuth app review
- Only works on Business/Creator accounts you control
- Hashtag search: 30 unique hashtags/week per account
- Rate limit: 200 requests/hour
- Trending hashtags: use `GET /ig_hashtag_search` → `/{id}/top_media`
- No native "trending audio" endpoint — proxy via Reels engagement

**TikTok (Official API)**
- Official API does NOT expose trending sounds, viral hashtags, or discovery data
- Research API access is heavily gated (academic orgs only as of 2026)
- **Recommended path: third-party API** (see below)

**Recommended Third-Party APIs**
| Provider | Best For | Pricing | Trending Sounds? |
|---|---|---|---|
| EnsembleData | Multi-platform (IG + TT) | $100–$1,400/mo | ✅ Yes |
| LamaTok | TikTok-only, cheapest | $0.0006/req | ✅ Yes |
| TikHub | Pay-as-you-go | $0.001/req | ✅ Yes |
| Apify | Scraping infra | $1.70/1k results | ✅ Yes |

For a lean start: **EnsembleData** covers both platforms under one key.
For TikTok-only on a budget: **LamaTok** (100 free requests to validate).

---

## Environment Variables

Create a `.env` file at project root. Never commit this file.

```env
# ── Instagram (Meta Graph API) ──────────────────────────────
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
INSTAGRAM_ACCESS_TOKEN=your_long_lived_token   # 60-day expiry — auto-refresh needed
INSTAGRAM_USER_ID=your_ig_business_user_id
INSTAGRAM_API_VERSION=v21.0

# ── TikTok (via Third-Party) ─────────────────────────────────
# Use ONE of the following blocks:

# Option A: EnsembleData (covers IG + TT)
ENSEMBLEDATA_API_TOKEN=your_ensembledata_token

# Option B: LamaTok (TikTok-only, cheaper)
LAMATOK_API_KEY=your_lamatok_key

# ── Email Delivery (SendGrid) ────────────────────────────────
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_FROM=trends@yourdomain.com
EMAIL_TO=you@yourdomain.com,teammate@yourdomain.com  # comma-separated

# ── Scheduler Config ─────────────────────────────────────────
REPORT_SCHEDULE=0 8 * * 1,3,5   # cron: Mon/Wed/Fri at 8am
TIMEZONE=Europe/London

# ── Claude API (for narrative summaries) ────────────────────
ANTHROPIC_API_KEY=your_anthropic_api_key

# ── App Config ───────────────────────────────────────────────
HASHTAGS_TO_TRACK=skincare,aestheticfashion,cottagecore,cleanbeauty
TIKTOK_REGIONS=GB,US                          # comma-separated country codes
LOG_FILE=data/trends_log.json
```

---

## Project Structure

```
social-trend-finder/
├── skill/
│   └── SKILL.md                  ← this file (importable into Claude)
│
├── src/
│   ├── fetchers/
│   │   ├── instagram.py          ← Meta Graph API calls
│   │   ├── tiktok.py             ← EnsembleData / LamaTok calls
│   │   └── base_fetcher.py       ← shared retry + rate-limit logic
│   │
│   ├── analysis/
│   │   ├── scorer.py             ← engagement velocity scoring
│   │   └── summariser.py         ← Claude API calls for trend narratives
│   │
│   └── email/
│       ├── renderer.py           ← HTML digest template
│       └── sender.py             ← SendGrid delivery
│
├── config/
│   └── settings.py               ← loads + validates env vars
│
├── data/
│   └── trends_log.json           ← append-only run history (gitignore)
│
├── tests/
│   ├── test_instagram.py
│   └── test_tiktok.py
│
├── main.py                       ← entry point; orchestrates the workflow
├── scheduler.py                  ← APScheduler job definition
├── .env                          ← secrets (NEVER commit)
├── .env.example                  ← safe template to commit
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Dependencies (`requirements.txt`)

```
# HTTP
requests==2.32.3
httpx==0.27.0         # async-friendly alternative for parallel fetches

# Env / Config
python-dotenv==1.0.1

# Scheduling
APScheduler==3.10.4

# Email
sendgrid==6.11.0

# Data handling
pandas==2.2.2         # optional; useful for scoring/sorting

# Claude API
anthropic==0.28.0

# Utils
tenacity==8.3.0       # retry decorator for flaky API calls
pytz==2024.1          # timezone handling for scheduler
```

Install: `pip install -r requirements.txt`

---

## Key Endpoints by Platform

### Instagram
```
# Search hashtag → get node ID
GET https://graph.facebook.com/{API_VERSION}/ig_hashtag_search
  ?user_id={INSTAGRAM_USER_ID}
  &q={hashtag}
  &access_token={TOKEN}

# Get top media for hashtag
GET https://graph.facebook.com/{API_VERSION}/{hashtag_id}/top_media
  ?fields=id,media_type,like_count,comments_count,timestamp
  &access_token={TOKEN}

# Trending Reels proxy (own account only)
GET https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media
  ?fields=id,media_type,like_count,comments_count,plays,timestamp
  &access_token={TOKEN}
```

### TikTok via EnsembleData
```
# Trending sounds
GET https://ensembledata.com/apis/tt/music/trending
  ?token={ENSEMBLEDATA_TOKEN}&region={REGION}

# Trending hashtags
GET https://ensembledata.com/apis/tt/hashtag/search
  ?token={ENSEMBLEDATA_TOKEN}&name={hashtag}

# Keyword/video trend search
GET https://ensembledata.com/apis/tt/keyword/search
  ?token={ENSEMBLEDATA_TOKEN}&keyword={term}&period=7
```

---

## Engagement Velocity Scoring

Don't rank by raw likes. Score by **velocity** (engagement per hour since post):

```
velocity = (likes + comments + shares + saves) / hours_since_posted
trend_score = velocity * recency_weight   # recency_weight decays over 48h
```

This surfaces what's *accelerating* right now, not what's just old and popular.

---

## Scheduler Setup

Run on a schedule using APScheduler (no external cron needed):

```python
# scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from main import run_trend_report
import os

scheduler = BlockingScheduler(timezone=os.getenv("TIMEZONE", "Europe/London"))

scheduler.add_job(
    run_trend_report,
    "cron",
    # Default: Mon/Wed/Fri 8am — override via REPORT_SCHEDULE env var
    day_of_week="mon,wed,fri",
    hour=8,
    minute=0,
)

scheduler.start()
```

To deploy: run `python scheduler.py` as a background process, or containerise
with Docker and deploy to any always-on host (Railway, Render, Fly.io, etc.).

---

## Email Digest Format

Each email should contain:

```
Subject: 📈 Social Trends Digest — [Mon 16 Jun]

TIKTOK
──────
🔊 Top Trending Sounds (UK + US)
  1. [Sound Name] — Artist · X,XXX videos this week · ↑ 42% vs last week
  2. ...

#️⃣ Rising Hashtags
  1. #[hashtag] · X.Xm posts · velocity score: 84
  2. ...

🎯 Claude's Take: [2-sentence narrative — what this signals for content strategy]

INSTAGRAM
─────────
#️⃣ Tracked Hashtag Performance
  [hashtag] · top post likes: X,XXX · recent posts: XXX · engagement rate: X.X%

📱 Format Trends
  [e.g. "Reels with text overlays outperforming static by 3x this week"]

🎯 Claude's Take: [2-sentence narrative]

──
Generated [timestamp] · Next report [next scheduled time]
Unsubscribe · Settings
```

---

## Claude Summary Prompt (used in `summariser.py`)

```python
SUMMARY_PROMPT = """
You are a social media trend analyst for a marketing team.
Given this trend data for {platform} this week:

{trend_data_json}

Write exactly 2 sentences:
1. What the data signals about audience behaviour or culture right now.
2. One actionable content recommendation the team should act on this week.

Be specific. No fluff. Use plain English, not marketing jargon.
"""
```

---

## Token Refresh (Instagram)

Instagram long-lived tokens expire in 60 days. Auto-refresh before expiry:

```python
# In instagram.py — call this weekly via scheduler
def refresh_instagram_token(current_token):
    url = "https://graph.facebook.com/oauth/access_token"
    params = {
        "grant_type": "ig_refresh_token",
        "access_token": current_token,
    }
    resp = requests.get(url, params=params)
    return resp.json().get("access_token")
```

Store the refreshed token back to `.env` or a secrets manager.

---

## Limitations & Gotchas

| Issue | Mitigation |
|---|---|
| Instagram: 30 hashtag searches/week | Pre-select hashtags carefully; rotate sets |
| TikTok official API: no trending data | Use EnsembleData or LamaTok |
| TikTok access token: 24h silent expiry | Build explicit refresh + monitoring |
| Instagram Insights: 1,000+ followers required | Only works on established accounts |
| Meta deprecated several Insights metrics Jan 2025 | Don't use `video_views` on non-Reels |
| Rate limits may cause partial runs | Use `tenacity` retries + partial-result logging |

---

## Running the Skill

```bash
# One-off run (test)
python main.py --once

# Start scheduled runner
python scheduler.py

# Run with Docker
docker build -t trend-finder .
docker run --env-file .env trend-finder python scheduler.py
```

---

## References
- Instagram Graph API: https://developers.facebook.com/docs/instagram-api
- Meta deprecated metrics (Jan 2025): https://developers.facebook.com/docs/instagram-api/changelog
- EnsembleData docs: https://ensembledata.com/docs
- LamaTok docs: https://api.lamatok.com/docs
- TikTok for Developers: https://developers.tiktok.com
- APScheduler docs: https://apscheduler.readthedocs.io
- SendGrid Python SDK: https://docs.sendgrid.com/for-developers/sending-email/v3-python-code-example
