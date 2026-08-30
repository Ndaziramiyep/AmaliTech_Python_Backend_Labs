from django.contrib.auth import get_user_model
from django.test import TestCase

from url_shortener.services.code_generator import RandomShortCodeGenerator
from url_shortener.services.url_shortener_service import UrlShortenerService

User = get_user_model()


class RandomShortCodeGeneratorTest(TestCase):
    def test_generate_default_length(self):
        code = RandomShortCodeGenerator().generate()
        self.assertEqual(len(code), 6)

    def test_generate_custom_length(self):
        code = RandomShortCodeGenerator(length=10).generate()
        self.assertEqual(len(code), 10)


class UrlShortenerServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="password123")

    def test_create_short_url(self):
        url_obj = UrlShortenerService().create_short_url("https://www.google.com", self.user)
        self.assertEqual(url_obj.original_url, "https://www.google.com")
        self.assertEqual(len(url_obj.short_code), 6)
        self.assertEqual(url_obj.owner, self.user)

    def test_create_with_custom_alias(self):
        url_obj = UrlShortenerService().create_short_url(
            "https://www.google.com", self.user, custom_alias="mylink"
        )
        self.assertEqual(url_obj.short_code, "mylink")
        self.assertEqual(url_obj.custom_alias, "mylink")

    def test_resolve_existing_short_code(self):
        service = UrlShortenerService()
        url_obj = service.create_short_url("https://www.example.com", self.user)
        self.assertEqual(service.resolve(url_obj.short_code), "https://www.example.com")

    def test_resolve_unknown_short_code(self):
        self.assertIsNone(UrlShortenerService().resolve("missing"))
