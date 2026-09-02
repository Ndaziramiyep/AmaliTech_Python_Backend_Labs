from django.test import TestCase

from url_shortener.services.code_generator import RandomShortCodeGenerator
from url_shortener.services.url_shortener_service import UrlShortenerService


class RandomShortCodeGeneratorTest(TestCase):
    def test_generate_default_length(self):
        code = RandomShortCodeGenerator().generate()
        self.assertEqual(len(code), 6)

    def test_generate_custom_length(self):
        code = RandomShortCodeGenerator(length=10).generate()
        self.assertEqual(len(code), 10)


class UrlShortenerServiceTest(TestCase):
    def setUp(self):
        self.owner_id = 1
        self.owner_email = "alice@example.com"

    def test_create_short_url(self):
        url_obj = UrlShortenerService().create_short_url(
            "https://www.google.com", self.owner_id, self.owner_email
        )
        self.assertEqual(url_obj.original_url, "https://www.google.com")
        self.assertEqual(len(url_obj.short_url), 6)
        self.assertEqual(url_obj.owner_id, self.owner_id)
        self.assertEqual(url_obj.owner_email, self.owner_email)

    def test_resolve_existing_short_code(self):
        service = UrlShortenerService()
        url_obj = service.create_short_url(
            "https://www.example.com", self.owner_id, self.owner_email
        )
        result = service.resolve(url_obj.short_url)
        self.assertEqual(result["original_url"], "https://www.example.com")
        self.assertEqual(result["owner_id"], self.owner_id)
        self.assertEqual(result["owner_email"], self.owner_email)

    def test_resolve_unknown_short_code(self):
        self.assertIsNone(UrlShortenerService().resolve("missing"))
