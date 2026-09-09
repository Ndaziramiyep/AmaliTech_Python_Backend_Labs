from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from preview.fetcher import PreviewFetchError

INTERNAL_KEY = "test-internal-key"


@override_settings(INTERNAL_API_KEY=INTERNAL_KEY)
class PreviewViewTest(APITestCase):
    """Tests the internal-only preview endpoint's auth gate and success/failure responses."""

    def test_requires_internal_key(self):
        response = self.client.post(reverse('url-preview'), {"url": "https://example.com/"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejects_wrong_internal_key(self):
        response = self.client.post(
            reverse('url-preview'), {"url": "https://example.com/"}, format='json', HTTP_X_INTERNAL_KEY='wrong',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejects_invalid_url(self):
        response = self.client.post(
            reverse('url-preview'), {"url": "not-a-url"}, format='json', HTTP_X_INTERNAL_KEY=INTERNAL_KEY,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('preview.views.fetch_preview')
    def test_success_returns_preview(self, mock_fetch_preview):
        mock_fetch_preview.return_value = {
            "title": "Example Domain", "description": "An example.", "favicon": "https://example.com/favicon.ico",
        }

        response = self.client.post(
            reverse('url-preview'), {"url": "https://example.com/"}, format='json', HTTP_X_INTERNAL_KEY=INTERNAL_KEY,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Example Domain")
        mock_fetch_preview.assert_called_once_with("https://example.com/")

    @patch('preview.views.fetch_preview')
    def test_fetch_failure_returns_502(self, mock_fetch_preview):
        mock_fetch_preview.side_effect = PreviewFetchError("connection refused")

        response = self.client.post(
            reverse('url-preview'), {"url": "https://dead-site.example/"}, format='json', HTTP_X_INTERNAL_KEY=INTERNAL_KEY,
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
