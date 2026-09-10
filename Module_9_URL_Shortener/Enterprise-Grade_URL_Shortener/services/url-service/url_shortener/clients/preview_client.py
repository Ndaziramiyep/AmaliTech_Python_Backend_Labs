import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

PREVIEW_REQUEST_TIMEOUT_SECONDS = 8


def fetch_preview(url: str):
    """Requests title/description/favicon for url from url-preview.

    Returns None (never raises) on any failure — url-preview being slow,
    down, or refusing the URL (e.g. its own SSRF guard) must never break
    URL creation; the caller (fetch_url_preview_task) just leaves those
    fields unset when this returns None.
    """
    endpoint = f"{settings.URL_PREVIEW_SERVICE_URL.rstrip('/')}/api/v1/internal/preview/"
    headers = {"X-Internal-Token": settings.URL_PREVIEW_INTERNAL_TOKEN}
    try:
        response = requests.post(
            endpoint, json={"url": url}, headers=headers, timeout=PREVIEW_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.warning("Failed to fetch preview for url=%s", url, exc_info=True)
        return None
    return response.json()
