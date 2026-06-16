# Social Trend Finder

Monitors Instagram and TikTok for trending hashtags and sounds.
Scores by engagement velocity. Delivers a digest email via SendGrid.

## Quick Start

```bash
git clone <your-repo>
cd social-trend-finder

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys

# Test once
python main.py --once

# Start scheduled runner (Mon/Wed/Fri 8am)
python scheduler.py
```

## API Keys You Need

| Key | Where to get it |
|---|---|
| META_APP_ID / META_APP_SECRET | developers.facebook.com → create app |
| INSTAGRAM_ACCESS_TOKEN | Meta Graph API Explorer → generate long-lived token |
| ENSEMBLEDATA_API_TOKEN | ensembledata.com (or use LAMATOK_API_KEY) |
| LAMATOK_API_KEY | api.lamatok.com (100 free requests) |
| SENDGRID_API_KEY | app.sendgrid.com → API Keys |
| ANTHROPIC_API_KEY | console.anthropic.com |

## Hashtag Limits

Instagram: 30 unique hashtags/week per account. Plan your list carefully.

## Deployment

Any always-on host works. Recommended options:
- **Railway** — push to GitHub, deploy, set env vars in dashboard
- **Render** — background worker, free tier available
- **Fly.io** — Docker-based, cheap for small workloads

## Skill Import

To use as a Claude skill, import `skill/SKILL.md` into your Claude setup.
The skill documents all endpoints, env vars, and the full workflow.
