import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

CLICK_EVENT_TIMEOUT_SECONDS = 1


def record_click(short_code: str, owner_id: int, referrer: str = "", user_agent: str = "", ip_address=None) -> None:
    """
    Fire-and-forget notification to analytics-service that a short link was
    visited. Never raises: a redirect must succeed even if analytics-service
    is unreachable, slow, or down.
    """
    url = f"{settings.ANALYTICS_SERVICE_URL.rstrip('/')}/api/events/click/"
    payload = {
        "short_code": short_code,
        "owner_id": owner_id,
        "referrer": referrer,
        "user_agent": user_agent,
        "ip_address": ip_address,
    }
    headers = {"X-Internal-Key": settings.INTERNAL_API_KEY}
    try:
        requests.post(url, json=payload, headers=headers, timeout=CLICK_EVENT_TIMEOUT_SECONDS)
    except requests.RequestException:
        logger.warning("Failed to record click event for short_code=%s", short_code, exc_info=True)
