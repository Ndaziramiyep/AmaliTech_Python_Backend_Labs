import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings

from apps.preview.api.services.errors import PreviewFetchError

logger = logging.getLogger(__name__)

USER_AGENT = "URLShortenerPreviewBot/1.0"


class HTMLPreviewFetcher:
    """Performs a single preview-fetch attempt against a destination URL. Never retries itself — PreviewService wraps it in retry/backoff."""

    def fetch(self, url: str) -> dict:
        """Streams one GET (capped at PREVIEW_MAX_BODY_BYTES) and parses title/description/favicon out of the response.

        Raises PreviewFetchError for a network error, a non-2xx response, or
        a non-HTML Content-Type.
        """
        try:
            response = requests.get(
                url,
                timeout=settings.PREVIEW_FETCH_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
                stream=True,
            )
        except requests.RequestException as exc:
            raise PreviewFetchError(f"request to {url} failed: {exc}") from exc

        try:
            if not response.ok:
                raise PreviewFetchError(f"{url} returned HTTP {response.status_code}")

            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                raise PreviewFetchError(f"{url} returned non-HTML content-type {content_type!r}")

            raw = response.raw.read(settings.PREVIEW_MAX_BODY_BYTES, decode_content=True)
            html = raw.decode(response.encoding or "utf-8", errors="replace")
            resolved_url = response.url
        finally:
            response.close()

        return self._parse(html, resolved_url)

    def _parse(self, html: str, base_url: str) -> dict:
        """Extracts <title>, a meta-description (og: preferred), and a favicon href from an HTML document."""
        soup = BeautifulSoup(html, "html.parser")

        title = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()[:255] or None

        description = None
        meta = soup.find("meta", attrs={"property": "og:description"}) or soup.find(
            "meta", attrs={"name": "description"}
        )
        if meta and meta.get("content"):
            description = meta["content"].strip()[:500] or None

        return {
            "title": title,
            "description": description,
            "favicon": self._extract_favicon(soup, base_url),
        }

    def _extract_favicon(self, soup, base_url: str) -> str:
        """Picks the best <link rel="icon"-ish> href, falling back to {scheme}://{netloc}/favicon.ico.

        Ignores a data: URI — some pages deliberately declare
        `<link rel="icon" href="data:,">` to tell a *browser* not to bother
        requesting one; that's not a usable image URL here.
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

        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
