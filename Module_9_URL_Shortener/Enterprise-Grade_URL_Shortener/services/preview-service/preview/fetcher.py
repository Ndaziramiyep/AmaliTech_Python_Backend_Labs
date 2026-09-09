import logging
import threading
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

FETCH_TIMEOUT_SECONDS = 5
# Read at most this many bytes of the response body — a page's <head> is
# always near the top, so there's no need to download an arbitrarily large
# page just to find its title/description/favicon.
MAX_CONTENT_BYTES = 1_000_000
USER_AGENT = "URLShortenerPreviewBot/1.0"

# Per-domain circuit breaker: a domain that keeps failing trips its own
# breaker independently of every other domain (one dead site shouldn't make
# previews of every other site fail too).
DOMAIN_CIRCUIT_FAILURE_THRESHOLD = 3
DOMAIN_CIRCUIT_RECOVERY_TIMEOUT_SECONDS = 60


class PreviewFetchError(Exception):
    """The destination page couldn't be fetched or parsed — retryable by the caller after backing off."""


class _DomainCircuitBreaker:
    """Circuit breaker keyed per-domain: each domain opens/closes independently, based only on its own recent failures."""

    def __init__(self, failure_threshold, recovery_timeout_seconds):
        self._failure_threshold = failure_threshold
        self._recovery_timeout_seconds = recovery_timeout_seconds
        self._state = {}
        self._lock = threading.Lock()

    def is_open(self, domain):
        with self._lock:
            entry = self._state.get(domain)
            if not entry or entry["opened_at"] is None:
                return False
            if time.monotonic() - entry["opened_at"] < self._recovery_timeout_seconds:
                return True
            # Recovery window elapsed: half-open — let one trial call through.
            entry["opened_at"] = None
            entry["failures"] = 0
            return False

    def record_success(self, domain):
        with self._lock:
            self._state.pop(domain, None)

    def record_failure(self, domain):
        with self._lock:
            entry = self._state.setdefault(domain, {"failures": 0, "opened_at": None})
            entry["failures"] += 1
            if entry["failures"] >= self._failure_threshold and entry["opened_at"] is None:
                entry["opened_at"] = time.monotonic()


_domain_circuit = _DomainCircuitBreaker(DOMAIN_CIRCUIT_FAILURE_THRESHOLD, DOMAIN_CIRCUIT_RECOVERY_TIMEOUT_SECONDS)


def _build_session():
    """A requests Session that retries a connection failure or 5xx response with exponential backoff before giving up."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_session = _build_session()


def _extract_favicon(soup, base_url):
    """Picks the best <link rel="icon"-ish> href, preferring an explicit icon link over an apple-touch-icon, falling back to /favicon.ico.

    Ignores a data: URI — some pages (e.g. example.com) deliberately declare
    `<link rel="icon" href="data:,">` to tell a *browser* not to bother
    requesting one; that's not a usable image URL for our purposes, so it's
    treated the same as no icon link at all.
    """
    best_href = None
    best_rank = -1
    for link in soup.find_all("link"):
        rel_values = [v.lower() for v in (link.get("rel") or [])]
        href = link.get("href")
        if not href or href.startswith("data:") or not any("icon" in v for v in rel_values):
            continue
        rank = 2 if any(v in ("icon", "shortcut icon") for v in rel_values) else 1
        if rank > best_rank:
            best_rank, best_href = rank, href

    if best_href:
        return urljoin(base_url, best_href)
    return urljoin(base_url, "/favicon.ico")


def _extract_meta(html, base_url):
    """Parses title, meta-description, and favicon out of an HTML document."""
    soup = BeautifulSoup(html, "html.parser")

    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()[:255] or None

    description = None
    meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if meta_tag and meta_tag.get("content"):
        description = meta_tag["content"].strip()[:500] or None

    return {
        "title": title,
        "description": description,
        "favicon": _extract_favicon(soup, base_url),
    }


def fetch_preview(url: str) -> dict:
    """Fetches the destination page and extracts its title/description/favicon.

    Raises PreviewFetchError if the domain's circuit is open, or the fetch/parse
    ultimately fails after the session's own retries with backoff are exhausted.
    """
    domain = urlparse(url).netloc
    if _domain_circuit.is_open(domain):
        logger.warning("Circuit open for domain=%s; skipping preview fetch", domain)
        raise PreviewFetchError(f"circuit open for domain {domain}")

    response = None
    try:
        response = _session.get(
            url,
            timeout=FETCH_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
            stream=True,
        )
        response.raise_for_status()
        raw = response.raw.read(MAX_CONTENT_BYTES, decode_content=True)
        html = raw.decode(response.encoding or "utf-8", errors="replace")
    except requests.RequestException as exc:
        _domain_circuit.record_failure(domain)
        logger.warning("Failed to fetch preview for url=%s", url, exc_info=True)
        raise PreviewFetchError(str(exc)) from exc
    finally:
        if response is not None:
            response.close()

    _domain_circuit.record_success(domain)
    return _extract_meta(html, response.url)
