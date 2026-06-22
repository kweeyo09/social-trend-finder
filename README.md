# Social Trend Finder

A Claude skill that turns trends across **TikTok, Instagram Reels, YouTube
(Shorts + long-form), and Reddit** into a short, ranked digest and **emails it
to your team** for collaboration.

Claude itself writes the summaries — there's **no AI API key**. Trend data is
fetched **centrally** by a GitHub Action, so running the skill needs **no keys
for fetching**. The only credential a user needs is a **SendGrid key to send the
email**.

```
Central feed (GitHub Action, server-side)        →   Skill in Claude (per user)
 fetch 4 platforms → score → commit JSON              read feeds → summarise → email team
 [one ScrapeCreators key; YouTube+Reddit keyless]     [only a SendGrid key, stored locally]
```

## Use it (per user)

1. Install the skill in Claude:
   ```bash
   git clone https://github.com/kweeyo09/social-trend-finder.git ~/.claude/skills/social-trend-finder
   ```
2. In Claude, say **"set up social trend finder"** (or `/trends`). It walks you
   through setup conversationally — recipients, from address, and your SendGrid key.
3. Ask for your digest any time: **"send the trends digest."**

No `pip install` needed — the skill side uses only the Python standard library.

## Set up the central feed (admin, one-time)

The trend data is produced server-side so users don't need any fetch keys.

1. In the GitHub repo, add one **Secret**: `SCRAPECREATORS_API_KEY` (covers
   TikTok + Instagram; YouTube and Reddit are keyless).
2. Optionally add **Variables** to tune what's tracked: `HASHTAGS_TO_TRACK`,
   `TIKTOK_COUNTRIES`, `TIKTOK_INDUSTRY`, `REDDIT_SUBREDDITS`, `YOUTUBE_QUERIES`
   (sensible defaults exist if unset).
3. Open the **Actions** tab → *Generate Trend Feeds* → **Run workflow** to create
   the first `feed-*.json`. After that it runs on the schedule in
   [`.github/workflows/generate-feed.yml`](.github/workflows/generate-feed.yml).

## What's in here

| Path | Role |
|---|---|
| `SKILL.md` | The skill Claude runs (onboarding + digest workflow) |
| `prepare_digest.py` | Skill side: fetch feed + prompts + config → JSON (stdlib only) |
| `deliver.py` | Skill side: email the digest via SendGrid (stdlib only) |
| `prompts/*.md` | Plain-English summary instructions (editable) |
| `generate_feed.py` | Server side: fetch + score, run by the Action |
| `instagram.py`, `tiktok.py` (ScrapeCreators), `reddit.py`, `youtube.py` (keyless), `scorer.py`, `base_fetcher.py`, `settings.py` | Server-side fetch/score library |
| `feed-*.json` | The committed trend feeds (produced by the Action) |

See [SETUP_AND_REQUIREMENTS.txt](SETUP_AND_REQUIREMENTS.txt) for the full
dependency / key / testing reference.
