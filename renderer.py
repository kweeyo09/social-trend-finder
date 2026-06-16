"""
src/email/renderer.py
Renders the trend digest as an HTML email string.
"""

from datetime import datetime


def _sound_row(sound: dict, rank: int) -> str:
    title = sound.get("title") or sound.get("music_title") or "Unknown"
    author = sound.get("author") or sound.get("music_author") or ""
    count = int(sound.get("score", 0))
    region = sound.get("region", "")
    return f"""
    <tr>
      <td style="padding:6px 0; color:#666; width:24px;">{rank}.</td>
      <td style="padding:6px 0;">
        <strong>{title}</strong>
        {f'· <span style="color:#888">{author}</span>' if author else ''}
      </td>
      <td style="padding:6px 0; text-align:right; color:#888; font-size:13px;">
        {count:,} videos · {region}
      </td>
    </tr>"""


def _hashtag_row(ht: dict, platform: str, rank: int) -> str:
    tag = ht.get("hashtag", "")
    if platform == "instagram":
        metric = f"Peak velocity: {ht.get('peak_velocity', 0)}"
        count = f"{ht.get('recent_count', 0)} recent posts"
    else:
        views = ht.get("view_count", 0)
        metric = f"{views:,} views"
        count = f"{ht.get('video_count', 0):,} videos"

    return f"""
    <tr>
      <td style="padding:6px 0; color:#666; width:24px;">{rank}.</td>
      <td style="padding:6px 0;"><strong>#{tag}</strong></td>
      <td style="padding:6px 0; text-align:right; color:#888; font-size:13px;">
        {metric} · {count}
      </td>
    </tr>"""


def render_digest(
    ig_hashtags: list[dict],
    tt_sounds: list[dict],
    tt_hashtags: list[dict],
    ig_insight: str,
    tt_insight: str,
    run_time: datetime,
) -> str:
    date_str = run_time.strftime("%A %-d %B %Y")

    tt_sound_rows = "".join(
        _sound_row(s, i + 1) for i, s in enumerate(tt_sounds[:5])
    )
    tt_hashtag_rows = "".join(
        _hashtag_row(h, "tiktok", i + 1) for i, h in enumerate(tt_hashtags[:5])
    )
    ig_hashtag_rows = "".join(
        _hashtag_row(h, "instagram", i + 1) for i, h in enumerate(ig_hashtags[:5])
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Social Trends Digest — {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden;max-width:600px;">

        <!-- Header -->
        <tr>
          <td style="background:#111;padding:24px 32px;">
            <p style="margin:0;color:#888;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Social Trends Digest</p>
            <h1 style="margin:4px 0 0;color:#fff;font-size:22px;font-weight:600;">{date_str}</h1>
          </td>
        </tr>

        <!-- TikTok section -->
        <tr>
          <td style="padding:28px 32px 0;">
            <h2 style="margin:0 0 16px;font-size:16px;font-weight:700;color:#111;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">
              🎵 TikTok
            </h2>

            <h3 style="margin:0 0 8px;font-size:13px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:0.5px;">
              🔊 Trending Sounds
            </h3>
            <table width="100%" cellpadding="0" cellspacing="0">
              {tt_sound_rows if tt_sound_rows else '<tr><td style="color:#888;padding:8px 0;">No sound data this run.</td></tr>'}
            </table>

            <h3 style="margin:20px 0 8px;font-size:13px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:0.5px;">
              #️⃣ Tracked Hashtags
            </h3>
            <table width="100%" cellpadding="0" cellspacing="0">
              {tt_hashtag_rows if tt_hashtag_rows else '<tr><td style="color:#888;padding:8px 0;">No hashtag data this run.</td></tr>'}
            </table>

            <div style="background:#f8f8f8;border-left:3px solid #111;padding:12px 16px;margin:20px 0 0;border-radius:0 4px 4px 0;">
              <p style="margin:0;font-size:12px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:0.5px;">
                🎯 Claude's Take
              </p>
              <p style="margin:8px 0 0;font-size:14px;color:#333;line-height:1.6;">{tt_insight}</p>
            </div>
          </td>
        </tr>

        <!-- Instagram section -->
        <tr>
          <td style="padding:28px 32px 0;">
            <h2 style="margin:0 0 16px;font-size:16px;font-weight:700;color:#111;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">
              📷 Instagram
            </h2>

            <h3 style="margin:0 0 8px;font-size:13px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:0.5px;">
              #️⃣ Tracked Hashtags
            </h3>
            <table width="100%" cellpadding="0" cellspacing="0">
              {ig_hashtag_rows if ig_hashtag_rows else '<tr><td style="color:#888;padding:8px 0;">No hashtag data this run.</td></tr>'}
            </table>

            <div style="background:#f8f8f8;border-left:3px solid #111;padding:12px 16px;margin:20px 0 0;border-radius:0 4px 4px 0;">
              <p style="margin:0;font-size:12px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:0.5px;">
                🎯 Claude's Take
              </p>
              <p style="margin:8px 0 0;font-size:14px;color:#333;line-height:1.6;">{ig_insight}</p>
            </div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:24px 32px;border-top:1px solid #f0f0f0;margin-top:32px;">
            <p style="margin:0;font-size:12px;color:#aaa;">
              Generated {run_time.strftime("%-d %b %Y at %H:%M %Z")} · Social Trend Finder
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""
