from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase

from apps.preview.api.services.errors import PreviewFetchError
from apps.preview.api.services.fetcher import HTMLPreviewFetcher


def _make_response(html: bytes, *, status_code=200, content_type="text/html; charset=utf-8", url="https://example.com/page"):
    """Builds a MagicMock standing in for a streamed requests.Response."""
    response = MagicMock()
    response.ok = 200 <= status_code < 300
    response.status_code = status_code
    response.headers = {"Content-Type": content_type}
    response.encoding = "utf-8"
    response.url = url
    response.raw.read.return_value = html
    return response


class HTMLPreviewFetcherTests(SimpleTestCase):
    def setUp(self):
        self.fetcher = HTMLPreviewFetcher()

    @patch("apps.preview.api.services.fetcher.requests.get")
    def test_extracts_title_description_and_favicon(self, mock_get):
        html = b"""
        <html><head>
        <title>Example Title</title>
        <meta property="og:description" content="An example description">
        <link rel="icon" href="/static/icon.png">
        </head></html>
        """
        mock_get.return_value = _make_response(html)

        result = self.fetcher.fetch("https://example.com/page")

        self.assertEqual(result["title"], "Example Title")
        self.assertEqual(result["description"], "An example description")
        self.assertEqual(result["favicon"], "https://example.com/static/icon.png")

    @patch("apps.preview.api.services.fetcher.requests.get")
    def test_falls_back_to_name_description_when_og_missing(self, mock_get):
        html = b'<html><head><title>T</title><meta name="description" content="Fallback desc"></head></html>'
        mock_get.return_value = _make_response(html)

        result = self.fetcher.fetch("https://example.com/")

        self.assertEqual(result["description"], "Fallback desc")

    @patch("apps.preview.api.services.fetcher.requests.get")
    def test_missing_description_is_none(self, mock_get):
        html = b"<html><head><title>T</title></head></html>"
        mock_get.return_value = _make_response(html)

        result = self.fetcher.fetch("https://example.com/")

        self.assertIsNone(result["description"])

    @patch("apps.preview.api.services.fetcher.requests.get")
    def test_falls_back_to_favicon_ico_when_no_link_tag(self, mock_get):
        html = b"<html><head><title>T</title></head></html>"
        mock_get.return_value = _make_response(html, url="https://example.com/page")

        result = self.fetcher.fetch("https://example.com/page")

        self.assertEqual(result["favicon"], "https://example.com/favicon.ico")

    @patch("apps.preview.api.services.fetcher.requests.get")
    def test_ignores_a_data_uri_favicon_link(self, mock_get):
        html = b'<html><head><title>T</title><link rel="icon" href="data:,"></head></html>'
        mock_get.return_value = _make_response(html, url="https://example.com/")

        result = self.fetcher.fetch("https://example.com/")

        self.assertEqual(result["favicon"], "https://example.com/favicon.ico")

    @patch("apps.preview.api.services.fetcher.requests.get")
    def test_non_html_content_type_raises(self, mock_get):
        mock_get.return_value = _make_response(b'{"not": "html"}', content_type="application/json")

        with self.assertRaises(PreviewFetchError):
            self.fetcher.fetch("https://example.com/data.json")

    @patch("apps.preview.api.services.fetcher.requests.get")
    def test_non_2xx_response_raises(self, mock_get):
        mock_get.return_value = _make_response(b"", status_code=404)

        with self.assertRaises(PreviewFetchError):
            self.fetcher.fetch("https://example.com/missing")

    @patch("apps.preview.api.services.fetcher.requests.get")
    def test_connection_error_raises(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("boom")

        with self.assertRaises(PreviewFetchError):
            self.fetcher.fetch("https://example.com/")
