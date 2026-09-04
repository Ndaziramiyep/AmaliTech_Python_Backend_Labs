from django.test import TestCase

from url_shortener.models import Tag, Url


class UrlModelTest(TestCase):
    """Tests basic creation and field storage on the Url model."""

    def test_create_url(self):
        """Assert that a created Url instance stores its fields as given."""
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

    def test_defaults(self):
        """Assert that a new Url defaults to active, uncounted, and alias-free."""
        url = Url.objects.create(
            original_url="https://www.example.com",
            short_url="abc124",
            owner_id=1,
            owner_email="alice@example.com",
        )
        self.assertTrue(url.is_active)
        self.assertEqual(url.click_count, 0)
        self.assertIsNone(url.custom_alias)
        self.assertIsNone(url.expires_at)

    def test_tags_many_to_many(self):
        """Assert that a Url can be tagged with multiple Tags."""
        url = Url.objects.create(
            original_url="https://www.example.com",
            short_url="abc125",
            owner_id=1,
            owner_email="alice@example.com",
        )
        news = Tag.objects.create(name="news")
        tech = Tag.objects.create(name="tech")
        url.tags.set([news, tech])

        self.assertEqual(set(url.tags.values_list('name', flat=True)), {"news", "tech"})
        self.assertIn(url, news.urls.all())


class TagModelTest(TestCase):
    """Tests basic creation and string representation of the Tag model."""

    def test_str_returns_name(self):
        """Assert that a Tag's string representation is its name."""
        tag = Tag.objects.create(name="news")
        self.assertEqual(str(tag), "news")
