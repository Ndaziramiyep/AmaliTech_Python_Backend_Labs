from unittest.mock import patch

import requests
from django.test import TestCase

from url_shortener.clients import analytics_client
from url_shortener.clients.analytics_client import AnalyticsServiceUnavailable


class RecordClickResilienceTest(TestCase):
    """record_click's use of the resilient session and analytics-service circuit breaker."""

    def setUp(self):
        """Each test starts with a closed circuit, regardless of what an earlier test left behind."""
        analytics_client._analytics_circuit.record_success()

    def tearDown(self):
        analytics_client._analytics_circuit.record_success()

    @patch.object(analytics_client, "_session")
    def test_success_keeps_circuit_closed(self, mock_session):
        mock_session.post.return_value.raise_for_status.return_value = None

        analytics_client.record_click(short_code="abc123", owner_id=1)

        mock_session.post.assert_called_once()
        self.assertFalse(analytics_client._analytics_circuit.is_open())

    @patch.object(analytics_client, "_session")
    def test_connection_failure_raises_retryable_error(self, mock_session):
        mock_session.post.side_effect = requests.ConnectionError("boom")

        with self.assertRaises(AnalyticsServiceUnavailable):
            analytics_client.record_click(short_code="abc123", owner_id=1)

    @patch.object(analytics_client, "_session")
    def test_circuit_opens_after_threshold_and_short_circuits_further_calls(self, mock_session):
        mock_session.post.side_effect = requests.ConnectionError("boom")

        for _ in range(analytics_client.CIRCUIT_FAILURE_THRESHOLD):
            with self.assertRaises(AnalyticsServiceUnavailable):
                analytics_client.record_click(short_code="abc123", owner_id=1)
        self.assertEqual(mock_session.post.call_count, analytics_client.CIRCUIT_FAILURE_THRESHOLD)

        # Circuit is now open: the next call fails fast, without attempting the network call at all.
        with self.assertRaises(AnalyticsServiceUnavailable):
            analytics_client.record_click(short_code="abc123", owner_id=1)
        self.assertEqual(mock_session.post.call_count, analytics_client.CIRCUIT_FAILURE_THRESHOLD)


class DeleteClickEventsResilienceTest(TestCase):
    """delete_click_events shares record_click's circuit breaker, so failures here trip it too."""

    def setUp(self):
        analytics_client._analytics_circuit.record_success()

    def tearDown(self):
        analytics_client._analytics_circuit.record_success()

    @patch.object(analytics_client, "_session")
    def test_success_keeps_circuit_closed(self, mock_session):
        mock_session.delete.return_value.raise_for_status.return_value = None

        analytics_client.delete_click_events(["abc123"])

        mock_session.delete.assert_called_once()
        self.assertFalse(analytics_client._analytics_circuit.is_open())

    @patch.object(analytics_client, "_session")
    def test_connection_failure_raises_retryable_error(self, mock_session):
        mock_session.delete.side_effect = requests.ConnectionError("boom")

        with self.assertRaises(AnalyticsServiceUnavailable):
            analytics_client.delete_click_events(["abc123"])
