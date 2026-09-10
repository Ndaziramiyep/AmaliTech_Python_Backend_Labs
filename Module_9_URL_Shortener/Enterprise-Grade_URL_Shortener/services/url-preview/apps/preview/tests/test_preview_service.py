from unittest.mock import MagicMock, patch

import fakeredis
from django.test import SimpleTestCase, override_settings

from apps.preview.api.services.errors import CircuitOpenError, InvalidURLError, PreviewFetchError
from apps.preview.api.services.preview_service import PreviewService

# A fake public-IP resolution for "example.com" so these tests never depend
# on real network/DNS access.
_PUBLIC_ADDR_INFO = [(2, 1, 6, "", ("93.184.216.34", 0))]


@override_settings(
    PREVIEW_MAX_ATTEMPTS=3,
    PREVIEW_RETRY_BASE_DELAY=0,
    PREVIEW_CIRCUIT_FAILURE_THRESHOLD=2,
    PREVIEW_CIRCUIT_OPEN_SECONDS=60,
    PREVIEW_CACHE_TTL=600,
)
class PreviewServiceTests(SimpleTestCase):
    def setUp(self):
        self.redis = fakeredis.FakeStrictRedis(decode_responses=True)
        self.fetcher = MagicMock()
        self.service = PreviewService(self.redis, fetcher=self.fetcher)

    @patch("apps.preview.api.services.preview_service.socket.getaddrinfo", return_value=_PUBLIC_ADDR_INFO)
    def test_retries_then_succeeds(self, mock_getaddrinfo):
        good = {"title": "T", "description": "D", "favicon": "https://example.com/favicon.ico"}
        self.fetcher.fetch.side_effect = [PreviewFetchError("boom"), good]

        result = self.service.fetch("https://example.com/")

        self.assertEqual(result, good)
        self.assertEqual(self.fetcher.fetch.call_count, 2)

    @patch("apps.preview.api.services.preview_service.socket.getaddrinfo", return_value=_PUBLIC_ADDR_INFO)
    def test_retries_exhausted_raises_and_records_one_failure(self, mock_getaddrinfo):
        self.fetcher.fetch.side_effect = PreviewFetchError("boom")

        with self.assertRaises(PreviewFetchError):
            self.service.fetch("https://example.com/")

        # PREVIEW_MAX_ATTEMPTS attempts inside the one call, but only one
        # failure recorded against the circuit breaker for the whole call.
        self.assertEqual(self.fetcher.fetch.call_count, 3)

    @patch("apps.preview.api.services.preview_service.socket.getaddrinfo", return_value=_PUBLIC_ADDR_INFO)
    def test_short_circuits_without_calling_the_fetcher_once_breaker_is_open(self, mock_getaddrinfo):
        self.fetcher.fetch.side_effect = PreviewFetchError("boom")
        # PREVIEW_CIRCUIT_FAILURE_THRESHOLD=2 — two exhausted top-level calls
        # trips the breaker for this domain.
        for _ in range(2):
            with self.assertRaises(PreviewFetchError):
                self.service.fetch("https://example.com/")
        self.fetcher.fetch.reset_mock()

        with self.assertRaises(CircuitOpenError):
            self.service.fetch("https://example.com/")

        self.fetcher.fetch.assert_not_called()

    def test_ssrf_guard_rejects_a_private_ip_target(self):
        with self.assertRaises(InvalidURLError):
            self.service.fetch("http://127.0.0.1/")

        self.fetcher.fetch.assert_not_called()

    def test_ssrf_guard_rejects_a_non_http_scheme(self):
        with self.assertRaises(InvalidURLError):
            self.service.fetch("ftp://example.com/")

        self.fetcher.fetch.assert_not_called()
