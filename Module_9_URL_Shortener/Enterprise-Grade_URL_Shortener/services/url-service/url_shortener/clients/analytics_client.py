import logging

import requests
from django.conf import settings

from url_shortener.clients.resilience import CircuitBreaker, build_retrying_session

logger = logging.getLogger(__name__)

CLICK_EVENT_TIMEOUT_SECONDS = 3
GEOLOCATION_TIMEOUT_SECONDS = 2
# Free, no-API-key IP geolocation lookup. Fails closed (returns no location)
# for private/reserved IPs (e.g. 127.0.0.1 in local/dev use) and on any error.
GEOLOCATION_URL = "http://ip-api.com/json/{ip}"

# Circuit breaker for analytics-service: trips open after this many
# consecutive failures, then short-circuits further calls (no network
# attempt) until the recovery window elapses, so an outage doesn't queue up
# a pile of slow, doomed requests.
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_RECOVERY_TIMEOUT_SECONDS = 30


class AnalyticsServiceUnavailable(Exception):
    """analytics-service couldn't be reached (or the circuit is open) — retryable by the calling Celery task."""


_analytics_circuit = CircuitBreaker(CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT_SECONDS)
_session = build_retrying_session()


def _geolocate(ip_address):
    """Looks up the city/country for a public IP via a free geolocation API, returning (None, None) on failure."""
    if not ip_address:
        return None, None
    try:
        response = _session.get(
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
    """Notifies analytics-service (with best-effort geolocation) that a short link was visited. Called from a Celery task, never directly from the request path — raises AnalyticsServiceUnavailable on failure so that task can retry with backoff."""
    if _analytics_circuit.is_open():
        logger.warning("analytics-service circuit open; skipping click record for short_code=%s", short_code)
        raise AnalyticsServiceUnavailable("circuit open")

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
        response = _session.post(url, json=payload, headers=headers, timeout=CLICK_EVENT_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        _analytics_circuit.record_failure()
        logger.warning("Failed to record click event for short_code=%s", short_code, exc_info=True)
        raise AnalyticsServiceUnavailable(str(exc)) from exc
    _analytics_circuit.record_success()


def delete_click_events(short_codes: list) -> None:
    """Cascade-deletes analytics-service's click history for the given short codes. Called from a Celery task — raises AnalyticsServiceUnavailable on failure so that task can retry with backoff."""
    if _analytics_circuit.is_open():
        logger.warning("analytics-service circuit open; skipping cascade-delete for short_codes=%s", short_codes)
        raise AnalyticsServiceUnavailable("circuit open")

    url = f"{settings.ANALYTICS_SERVICE_URL.rstrip('/')}/api/v1/events/click/"
    headers = {"X-Internal-Key": settings.INTERNAL_API_KEY}
    try:
        response = _session.delete(
            url, json={"short_codes": short_codes}, headers=headers, timeout=CLICK_EVENT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        _analytics_circuit.record_failure()
        logger.warning("Failed to cascade-delete click events for short_codes=%s", short_codes, exc_info=True)
        raise AnalyticsServiceUnavailable(str(exc)) from exc
    _analytics_circuit.record_success()
