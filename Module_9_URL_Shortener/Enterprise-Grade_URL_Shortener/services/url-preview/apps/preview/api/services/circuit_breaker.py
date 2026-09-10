import logging

from apps.preview.api.services.errors import CircuitOpenError

logger = logging.getLogger(__name__)

# How long a domain's failure counter stays alive before resetting to zero —
# failures older than this no longer count toward tripping the breaker.
FAILURE_WINDOW_SECONDS = 120


class DomainCircuitBreaker:
    """Redis-backed circuit breaker keyed per destination domain, shared across replicas (not just one process's memory)."""

    def __init__(self, redis_client, failure_threshold: int, open_seconds: int):
        self._redis = redis_client
        self._failure_threshold = failure_threshold
        self._open_seconds = open_seconds

    def _fail_key(self, domain: str) -> str:
        return f"preview:circuit:fail:{domain}"

    def _open_key(self, domain: str) -> str:
        return f"preview:circuit:open:{domain}"

    def raise_if_open(self, domain: str) -> None:
        """Raises CircuitOpenError with no network call at all if this domain's circuit is currently open."""
        if self._redis.exists(self._open_key(domain)):
            logger.warning("Circuit open for domain=%s; skipping preview fetch", domain)
            raise CircuitOpenError(f"circuit open for domain {domain}")

    def record_failure(self, domain: str) -> None:
        """Increments the domain's sliding-window failure counter, opening the circuit once the threshold is reached."""
        key = self._fail_key(domain)
        count = self._redis.incr(key)
        if count == 1:
            self._redis.expire(key, FAILURE_WINDOW_SECONDS)
        if count >= self._failure_threshold:
            self._redis.setex(self._open_key(domain), self._open_seconds, "1")
            logger.warning("Circuit opened for domain=%s after %d failures", domain, count)

    def record_success(self, domain: str) -> None:
        """Clears both the open flag and the failure counter outright — a clean slate for this domain."""
        self._redis.delete(self._open_key(domain), self._fail_key(domain))
