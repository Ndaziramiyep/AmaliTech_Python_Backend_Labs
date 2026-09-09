from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase

from preview import fetcher
from preview.fetcher import PreviewFetchError, _extract_meta, fetch_preview

SAMPLE_HTML = """
<html>
<head>
    <title>  Example Domain  </title>
    <meta name="description" content="An example page for testing.">
    <link rel="shortcut icon" href="/static/favicon.ico">
    <link rel="apple-touch-icon" href="/static/apple-icon.png">
</head>
<body></body>
</html>
"""


class ExtractMetaTest(SimpleTestCase):
    """Tests HTML parsing in isolation from any network call."""

    def test_extracts_title_description_and_favicon(self):
        result = _extract_meta(SAMPLE_HTML, "https://example.com/page")

        self.assertEqual(result["title"], "Example Domain")
        self.assertEqual(result["description"], "An example page for testing.")
        self.assertEqual(result["favicon"], "https://example.com/static/favicon.ico")

    def test_prefers_explicit_icon_over_apple_touch_icon(self):
        html = """
        <html><head>
        <link rel="apple-touch-icon" href="/apple.png">
        <link rel="icon" href="/favicon.png">
        </head></html>
        """
        result = _extract_meta(html, "https://example.com/")
        self.assertEqual(result["favicon"], "https://example.com/favicon.png")

    def test_falls_back_to_default_favicon_path(self):
        html = "<html><head><title>No Icon</title></head></html>"
        result = _extract_meta(html, "https://example.com/")
        self.assertEqual(result["favicon"], "https://example.com/favicon.ico")

    def test_ignores_a_data_uri_favicon(self):
        """example.com and others deliberately declare href="data:," to tell a browser not to request one — that's not a usable image URL, so fall back like there was no icon link at all."""
        html = '<html><head><link rel="icon" href="data:,"></head></html>'
        result = _extract_meta(html, "https://example.com/")
        self.assertEqual(result["favicon"], "https://example.com/favicon.ico")

    def test_missing_title_and_description_are_none(self):
        html = "<html><head></head></html>"
        result = _extract_meta(html, "https://example.com/")
        self.assertIsNone(result["title"])
        self.assertIsNone(result["description"])


class FetchPreviewResilienceTest(SimpleTestCase):
    """fetch_preview's use of the resilient session and per-domain circuit breaker."""

    def setUp(self):
        """Each test starts with every domain's circuit closed, regardless of what an earlier test left behind."""
        fetcher._domain_circuit._state.clear()

    def tearDown(self):
        fetcher._domain_circuit._state.clear()

    def _mock_response(self, html, url="https://example.com/"):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.raw.read.return_value = html.encode("utf-8")
        response.encoding = "utf-8"
        response.url = url
        return response

    @patch.object(fetcher, "_session")
    def test_success_returns_parsed_preview(self, mock_session):
        mock_session.get.return_value = self._mock_response(SAMPLE_HTML)

        result = fetch_preview("https://example.com/page")

        self.assertEqual(result["title"], "Example Domain")
        mock_session.get.assert_called_once()

    @patch.object(fetcher, "_session")
    def test_connection_failure_raises_preview_fetch_error(self, mock_session):
        mock_session.get.side_effect = requests.ConnectionError("boom")

        with self.assertRaises(PreviewFetchError):
            fetch_preview("https://dead-site.example/")

    @patch.object(fetcher, "_session")
    def test_circuit_opens_after_threshold_and_short_circuits_further_calls(self, mock_session):
        mock_session.get.side_effect = requests.ConnectionError("boom")

        for _ in range(fetcher.DOMAIN_CIRCUIT_FAILURE_THRESHOLD):
            with self.assertRaises(PreviewFetchError):
                fetch_preview("https://dead-site.example/")
        self.assertEqual(mock_session.get.call_count, fetcher.DOMAIN_CIRCUIT_FAILURE_THRESHOLD)

        # Circuit is now open for dead-site.example: the next call fails fast, without attempting the network call at all.
        with self.assertRaises(PreviewFetchError):
            fetch_preview("https://dead-site.example/")
        self.assertEqual(mock_session.get.call_count, fetcher.DOMAIN_CIRCUIT_FAILURE_THRESHOLD)

    @patch.object(fetcher, "_session")
    def test_other_domains_are_unaffected_by_one_domains_open_circuit(self, mock_session):
        mock_session.get.side_effect = requests.ConnectionError("boom")
        for _ in range(fetcher.DOMAIN_CIRCUIT_FAILURE_THRESHOLD):
            with self.assertRaises(PreviewFetchError):
                fetch_preview("https://dead-site.example/")

        mock_session.get.side_effect = None
        mock_session.get.return_value = self._mock_response(SAMPLE_HTML, url="https://healthy-site.example/")

        result = fetch_preview("https://healthy-site.example/")
        self.assertEqual(result["title"], "Example Domain")
