import hashlib
import ipaddress
import json
import logging
import socket
from urllib.parse import urlparse

from django.conf import settings

from apps.preview.api.services.circuit_breaker import DomainCircuitBreaker
from apps.preview.api.services.errors import InvalidURLError, PreviewFetchError
from apps.preview.api.services.fetcher import HTMLPreviewFetcher
from apps.preview.api.services.retry import call_with_backoff

logger = logging.getLogger(__name__)


def _cache_key(url: str) -> str:
    return f"preview:cache:{hashlib.sha256(url.encode()).hexdigest()}"


class PreviewService:
    """Orchestrates one preview fetch: validates the URL, guards against SSRF, checks the result cache, consults the circuit breaker, then retries the fetch."""

    def __init__(self, redis_client, fetcher=None, circuit_breaker=None):
        self._redis = redis_client
        self._fetcher = fetcher or HTMLPreviewFetcher()
        self._circuit_breaker = circuit_breaker or DomainCircuitBreaker(
            redis_client,
            failure_threshold=settings.PREVIEW_CIRCUIT_FAILURE_THRESHOLD,
            open_seconds=settings.PREVIEW_CIRCUIT_OPEN_SECONDS,
        )

    def fetch(self, url: str) -> dict:
        """Returns {"title", "description", "favicon"} for url.

        Raises InvalidURLError (SSRF guard / malformed URL), CircuitOpenError
        (destination domain's circuit is open), or PreviewFetchError (fetch
        failed after every retry attempt).
        """
        domain = self._validate_and_resolve(url)

        cached = self._redis.get(_cache_key(url))
        if cached is not None:
            return json.loads(cached)

        self._circuit_breaker.raise_if_open(domain)

        try:
            result = call_with_backoff(
                lambda: self._fetcher.fetch(url),
                max_attempts=settings.PREVIEW_MAX_ATTEMPTS,
                base_delay=settings.PREVIEW_RETRY_BASE_DELAY,
                retryable_exceptions=(PreviewFetchError,),
            )
        except PreviewFetchError:
            self._circuit_breaker.record_failure(domain)
            raise

        self._circuit_breaker.record_success(domain)
        # Failures are never cached — a transient outage shouldn't get
        # "stuck" negative once the destination recovers.
        self._redis.setex(_cache_key(url), settings.PREVIEW_CACHE_TTL, json.dumps(result))
        return result

    def _validate_and_resolve(self, url: str) -> str:
        """Resolves url's hostname and rejects it if any resolved address is private/loopback/link-local/reserved/multicast.

        A DNS resolution failure is wrapped as InvalidURLError too, rather
        than leaking a raw socket exception — this service fetches arbitrary
        attacker-influenceable URLs into the internal Docker network, so a
        URL pointed at 169.254.169.254 or 127.0.0.1 must never reach
        requests.get.
        """
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise InvalidURLError(f"{url!r} is not a valid http(s) URL")

        hostname = parsed.hostname
        try:
            addr_infos = socket.getaddrinfo(hostname, None)
        except socket.gaierror as exc:
            raise InvalidURLError(f"could not resolve host {hostname!r}: {exc}") from exc

        for _family, _type, _proto, _canonname, sockaddr in addr_infos:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise InvalidURLError(f"{hostname!r} resolves to a disallowed address {ip}")

        return hostname
