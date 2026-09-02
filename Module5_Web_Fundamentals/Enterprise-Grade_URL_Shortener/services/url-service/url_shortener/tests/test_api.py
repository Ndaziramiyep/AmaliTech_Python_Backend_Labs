from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from url_shortener.models import Url


class CreateShortUrlAPITest(APITestCase):
    def test_create_success(self):
        data = {
            'original_url': 'https://www.example.com',
            'owner_id': 1,
            'owner_email': 'alice@example.com',
        }
        response = self.client.post(reverse('create-short-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('short_url', response.data)
        self.assertIn('short_link', response.data)
        self.assertEqual(response.data['owner'], 'alice@example.com')

    def test_missing_owner(self):
        data = {'original_url': 'https://www.example.com'}
        response = self.client.post(reverse('create-short-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_url(self):
        data = {
            'original_url': 'not-a-valid-url',
            'owner_id': 1,
            'owner_email': 'alice@example.com',
        }
        response = self.client.post(reverse('create-short-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RedirectUrlAPITest(APITestCase):
    def setUp(self):
        Url.objects.create(
            original_url="https://www.example.com",
            short_url="test123",
            owner_id=2,
            owner_email="bob@example.com",
        )

    @patch('url_shortener.api.views.analytics_client.record_click')
    def test_redirect_success(self, mock_record_click):
        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'test123'}))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "https://www.example.com")
        mock_record_click.assert_called_once()
        self.assertEqual(mock_record_click.call_args.kwargs['short_code'], 'test123')
        self.assertEqual(mock_record_click.call_args.kwargs['owner_id'], 2)

    def test_redirect_not_found(self):
        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'invalid'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
