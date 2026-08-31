from django.test import TestCase

from url_shortener.models import Url


class UrlModelTest(TestCase):
    def test_create_url(self):
        url = Url.objects.create(
            original_url="https://www.example.com",
            short_url="abc123",
            owner_id=1,
            owner_email="alice@example.com",
        )
        self.assertEqual(url.original_url, "https://www.example.com")
        self.assertEqual(url.short_url, "abc123")
        self.assertEqual(url.owner_id, 1)
        self.assertEqual(url.owner_email, "alice@example.com")
