import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

CLICK_EVENT_TIMEOUT_SECONDS = 3
GEOLOCATION_TIMEOUT_SECONDS = 2
# Free, no-API-key IP geolocation lookup. Fails closed (returns no location)
# for private/reserved IPs (e.g. 127.0.0.1 in local/dev use) and on any error.
GEOLOCATION_URL = "http://ip-api.com/json/{ip}"


def _geolocate(ip_address):
    """Looks up the city/country for a public IP via a free geolocation API, returning (None, None) on failure."""
    if not ip_address:
        return None, None
    try:
        response = requests.get(
            GEOLOCATION_URL.format(ip=ip_address),
            params={"fields": "status,city,country"},
            timeout=GEOLOCATION_TIMEOUT_SECONDS,
        )
        data = response.json()
    except (requests.RequestException, ValueError):
        logger.warning("Geolocation lookup failed for ip=%s", ip_address, exc_info=True)
        return None, None

    if data.get("status") != "success":
        return None, None
    return data.get("city"), data.get("country")


def record_click(short_code: str, owner_id: int, referrer: str = "", user_agent: str = "", ip_address=None) -> None:
    """Fire-and-forget notification to analytics-service (with best-effort geolocation) that a short link was visited; called from a background thread, so it never blocks the redirect and never raises."""
    city, country = _geolocate(ip_address)
    url = f"{settings.ANALYTICS_SERVICE_URL.rstrip('/')}/api/v1/events/click/"
    payload = {
        "short_code": short_code,
        "owner_id": owner_id,
        "referrer": referrer,
        "user_agent": user_agent,
        "ip_address": ip_address,
        "city": city,
        "country": country,
    }
    headers = {"X-Internal-Key": settings.INTERNAL_API_KEY}
    try:
        requests.post(url, json=payload, headers=headers, timeout=CLICK_EVENT_TIMEOUT_SECONDS)
    except requests.RequestException:
        logger.warning("Failed to record click event for short_code=%s", short_code, exc_info=True)


def delete_click_events(short_codes: list) -> None:
    """Fire-and-forget request to cascade-delete analytics-service's click history for the given short codes."""
    url = f"{settings.ANALYTICS_SERVICE_URL.rstrip('/')}/api/v1/events/click/"
    headers = {"X-Internal-Key": settings.INTERNAL_API_KEY}
    try:
        requests.delete(url, json={"short_codes": short_codes}, headers=headers, timeout=CLICK_EVENT_TIMEOUT_SECONDS)
    except requests.RequestException:
        logger.warning("Failed to cascade-delete click events for short_codes=%s", short_codes, exc_info=True)
