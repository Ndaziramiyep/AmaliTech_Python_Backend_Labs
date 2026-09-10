from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient


@override_settings(INTERNAL_SERVICE_TOKEN="test-internal-token")
class PreviewEndpointSmokeTests(TestCase):
    """End-to-end coverage of POST /api/v1/internal/preview/ through Django's request/response cycle."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("url-preview-fetch")

    def test_missing_internal_token_is_rejected(self):
        response = self.client.post(self.url, {"url": "https://example.com/"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_wrong_internal_token_is_rejected(self):
        response = self.client.post(
            self.url, {"url": "https://example.com/"}, format="json",
            HTTP_X_INTERNAL_TOKEN="not-the-right-token",
        )
        self.assertEqual(response.status_code, 403)

    @patch("apps.preview.api.views.PreviewService")
    def test_valid_token_with_a_mocked_fetch_returns_200(self, mock_service_cls):
        mock_service_cls.return_value.fetch.return_value = {
            "title": "Example",
            "description": "An example page",
            "favicon": "https://example.com/favicon.ico",
        }

        response = self.client.post(
            self.url, {"url": "https://example.com/"}, format="json",
            HTTP_X_INTERNAL_TOKEN="test-internal-token",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "title": "Example",
                "description": "An example page",
                "favicon": "https://example.com/favicon.ico",
            },
        )

    def test_invalid_payload_returns_400(self):
        response = self.client.post(
            self.url, {"url": "not-a-url"}, format="json",
            HTTP_X_INTERNAL_TOKEN="test-internal-token",
        )
        self.assertEqual(response.status_code, 400)
