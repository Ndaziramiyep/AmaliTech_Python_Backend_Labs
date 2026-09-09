import logging

import requests
from django.conf import settings

from url_shortener.clients.resilience import CircuitBreaker, build_retrying_session

logger = logging.getLogger(__name__)

PREVIEW_FETCH_TIMEOUT_SECONDS = 8

# Circuit breaker for preview-service itself (not for the arbitrary
# destination sites it fetches on our behalf — that's a separate, per-domain
# breaker inside preview-service): trips open after this many consecutive
# failures reaching preview-service at all, so an outage there doesn't queue
# up a pile of slow, doomed requests.
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_RECOVERY_TIMEOUT_SECONDS = 30

_preview_circuit = CircuitBreaker(CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT_SECONDS)
_session = build_retrying_session(methods=("GET", "POST"))


class PreviewServiceUnavailable(Exception):
    """preview-service couldn't be reached (or the circuit is open) — retryable by the calling Celery task."""


def fetch_preview(original_url: str) -> dict:
    """Asks preview-service for the destination page's title/description/favicon.

    Raises PreviewServiceUnavailable if preview-service's circuit is open, it
    can't be reached, or it reports the destination page itself couldn't be
    fetched (its own per-domain circuit breaker, or the page being down) —
    all of these are retryable by the calling Celery task.
    """
    if _preview_circuit.is_open():
        logger.warning("preview-service circuit open; skipping preview fetch for url=%s", original_url)
        raise PreviewServiceUnavailable("circuit open")

    url = f"{settings.PREVIEW_SERVICE_URL.rstrip('/')}/api/v1/preview/"
    headers = {"X-Internal-Key": settings.INTERNAL_API_KEY}
    try:
        response = _session.post(
            url, json={"url": original_url}, headers=headers, timeout=PREVIEW_FETCH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        _preview_circuit.record_failure()
        logger.warning("Failed to fetch preview for url=%s", original_url, exc_info=True)
        raise PreviewServiceUnavailable(str(exc)) from exc

    _preview_circuit.record_success()
    return response.json()
