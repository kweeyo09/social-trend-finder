"""
summariser.py
Calls Claude claude-sonnet-4-6 to generate 2-sentence trend insights.
"""

import json
import logging
import anthropic
import settings

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

PROMPT_TEMPLATE = """
You are a social media trend analyst for a marketing team.
Given this trend data for {platform} this week:

{trend_data}

Write exactly 2 sentences:
1. What the data signals about audience behaviour or cultural interest right now.
2. One specific, actionable content recommendation the team should act on this week.

Rules:
- Be specific, not generic.
- No fluff, no marketing jargon.
- Plain English only.
- Do not say "it's clear that" or "it's important to".
"""


def generate_insight(platform: str, trend_data: dict) -> str:
    """
    Ask Claude to generate a 2-sentence trend insight.
    Returns the insight string, or a fallback on error.
    """
    prompt = PROMPT_TEMPLATE.format(
        platform=platform,
        trend_data=json.dumps(trend_data, indent=2, default=str)[:3000],  # cap tokens
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        logger.error(f"Claude summariser failed for {platform}: {e}")
        return "Unable to generate insight this run."
