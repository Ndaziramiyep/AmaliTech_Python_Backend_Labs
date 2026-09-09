from unittest.mock import patch

import requests
from django.test import TestCase

from url_shortener.clients import preview_client
from url_shortener.clients.preview_client import PreviewServiceUnavailable


class FetchPreviewResilienceTest(TestCase):
    """preview_client.fetch_preview's use of the resilient session and preview-service circuit breaker."""

    def setUp(self):
        """Each test starts with a closed circuit, regardless of what an earlier test left behind."""
        preview_client._preview_circuit.record_success()

    def tearDown(self):
        preview_client._preview_circuit.record_success()

    @patch.object(preview_client, "_session")
    def test_success_returns_parsed_preview(self, mock_session):
        mock_session.post.return_value.raise_for_status.return_value = None
        mock_session.post.return_value.json.return_value = {
            "title": "Example", "description": "An example.", "favicon": "https://example.com/favicon.ico",
        }

        result = preview_client.fetch_preview("https://example.com/")

        self.assertEqual(result["title"], "Example")
        mock_session.post.assert_called_once()
        self.assertFalse(preview_client._preview_circuit.is_open())

    @patch.object(preview_client, "_session")
    def test_connection_failure_raises_retryable_error(self, mock_session):
        mock_session.post.side_effect = requests.ConnectionError("boom")

        with self.assertRaises(PreviewServiceUnavailable):
            preview_client.fetch_preview("https://example.com/")

    @patch.object(preview_client, "_session")
    def test_circuit_opens_after_threshold_and_short_circuits_further_calls(self, mock_session):
        mock_session.post.side_effect = requests.ConnectionError("boom")

        for _ in range(preview_client.CIRCUIT_FAILURE_THRESHOLD):
            with self.assertRaises(PreviewServiceUnavailable):
                preview_client.fetch_preview("https://example.com/")
        self.assertEqual(mock_session.post.call_count, preview_client.CIRCUIT_FAILURE_THRESHOLD)

        # Circuit is now open: the next call fails fast, without attempting the network call at all.
        with self.assertRaises(PreviewServiceUnavailable):
            preview_client.fetch_preview("https://example.com/")
        self.assertEqual(mock_session.post.call_count, preview_client.CIRCUIT_FAILURE_THRESHOLD)
