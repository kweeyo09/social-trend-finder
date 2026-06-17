"""
base_fetcher.py
Shared HTTP helper used by instagram.py and tiktok.py.

Fetches over Scrapling (https://github.com/D4Vinci/Scrapling) instead of raw
requests, and wraps the call in tenacity for retry/backoff on rate limits
(HTTP 429) and transient server errors (5xx).

All API endpoints in this project return JSON, so safe_get() returns the
parsed JSON body as a dict.
"""

import logging
from scrapling.fetchers import Fetcher
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

# HTTP status codes worth retrying: rate limited, or transient server faults.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class RetryableHTTPError(Exception):
    """Raised on a retryable HTTP status so tenacity will try again."""


@retry(
    retry=retry_if_exception_type(RetryableHTTPError),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def safe_get(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = 15,
) -> dict:
    """
    GET `url` via Scrapling and return the JSON body as a dict.

    Retries up to 4 times with exponential backoff on 429/5xx responses.
    Non-retryable error statuses (e.g. 401, 404) raise immediately.
    """
    page = Fetcher.get(
        url,
        params=params or {},
        headers=headers or {},
        timeout=timeout,
    )

    if page.status in RETRYABLE_STATUS:
        logger.warning(f"Retryable status {page.status} from {url}")
        raise RetryableHTTPError(f"{page.status} from {url}")

    if page.status >= 400:
        # Non-retryable client error — surface it once, no point retrying.
        raise RuntimeError(f"HTTP {page.status} from {url}: {page.text[:200]}")

    return page.json()
