from django.contrib.auth.models import User
from django.test import TestCase

from url_shortener.models import Url


class UrlModelTest(TestCase):
    def test_create_url(self):
        owner = User.objects.create_user(username="alice", password="password123")
        url = Url.objects.create(
            original_url="https://www.example.com",
            short_url="abc123",
            owner=owner,
        )
        self.assertEqual(url.original_url, "https://www.example.com")
        self.assertEqual(url.short_url, "abc123")
        self.assertEqual(url.owner, owner)
