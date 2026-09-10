from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase

from url_shortener.clients import preview_client


class FetchPreviewTest(TestCase):
    """Tests preview_client.fetch_preview's request shape and its never-raises contract."""

    @patch('url_shortener.clients.preview_client.requests.post')
    def test_posts_the_url_with_the_internal_token_header(self, mock_post):
        mock_post.return_value = MagicMock(
            json=lambda: {"title": "T", "description": "D", "favicon": "https://example.com/favicon.ico"},
        )
        mock_post.return_value.raise_for_status.return_value = None

        result = preview_client.fetch_preview("https://example.com/")

        self.assertEqual(result["title"], "T")
        _args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json'], {"url": "https://example.com/"})
        self.assertIn('X-Internal-Token', kwargs['headers'])

    @patch('url_shortener.clients.preview_client.requests.post')
    def test_returns_none_without_raising_on_a_connection_error(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("boom")

        result = preview_client.fetch_preview("https://example.com/")

        self.assertIsNone(result)

    @patch('url_shortener.clients.preview_client.requests.post')
    def test_returns_none_without_raising_on_a_non_2xx_response(self, mock_post):
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError("502")
        mock_post.return_value = response

        result = preview_client.fetch_preview("https://example.com/")

        self.assertIsNone(result)
