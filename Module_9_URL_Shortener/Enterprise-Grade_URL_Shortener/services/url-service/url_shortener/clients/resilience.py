import threading
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CircuitBreaker:
    """Process-local circuit breaker: opens after N consecutive failures, half-opens for a trial call once the recovery timeout elapses.

    Shared by every client under url_shortener/clients/ that calls another
    service over HTTP — one instance per downstream dependency.
    """

    def __init__(self, failure_threshold, recovery_timeout_seconds):
        self._failure_threshold = failure_threshold
        self._recovery_timeout_seconds = recovery_timeout_seconds
        self._failures = 0
        self._opened_at = None
        self._lock = threading.Lock()

    def is_open(self):
        with self._lock:
            if self._opened_at is None:
                return False
            if time.monotonic() - self._opened_at < self._recovery_timeout_seconds:
                return True
            # Recovery window elapsed: half-open — let one trial call through.
            self._opened_at = None
            self._failures = 0
            return False

    def record_success(self):
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self):
        with self._lock:
            self._failures += 1
            if self._failures >= self._failure_threshold and self._opened_at is None:
                self._opened_at = time.monotonic()


def build_retrying_session(methods=("GET", "POST", "DELETE")):
    """A requests Session that retries a connection failure or 5xx response with exponential backoff, so a brief downstream blip doesn't fail the whole call."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(502, 503, 504),
        allowed_methods=frozenset(methods),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
