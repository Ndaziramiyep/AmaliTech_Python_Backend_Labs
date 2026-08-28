from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from url_shortener.models import Url


class CreateShortUrlAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="password123"
        )
        self.access_token = str(RefreshToken.for_user(self.user).access_token)

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_create_requires_authentication(self):
        data = {'original_url': 'https://www.example.com'}
        response = self.client.post(reverse('create-short-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_success(self):
        self.authenticate()
        data = {'original_url': 'https://www.example.com'}
        response = self.client.post(reverse('create-short-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('short_url', response.data)
        self.assertIn('short_link', response.data)
        self.assertEqual(response.data['owner'], 'alice')

    def test_invalid_url(self):
        self.authenticate()
        data = {'original_url': 'not-a-valid-url'}
        response = self.client.post(reverse('create-short-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RedirectUrlAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bob", password="password123")

    def test_redirect_success(self):
        Url.objects.create(
            original_url="https://www.example.com",
            short_url="test123",
            owner=self.user,
        )
        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'test123'}))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "https://www.example.com")

    def test_redirect_not_found(self):
        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'invalid'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
