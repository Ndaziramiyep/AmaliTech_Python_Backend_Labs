from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from url_shortener.caching import cache_key, cache_url
from url_shortener.models import Url
from url_shortener.tasks import archive_expired_urls, fetch_url_preview_task


class ArchiveExpiredUrlsTaskTest(TestCase):
    """Tests the nightly Celery Beat cleanup task that archives past-expiry URLs."""

    def setUp(self):
        """Clear the shared cache before each test — it isn't rolled back between tests like the DB is."""
        cache.clear()

    def test_archives_expired_url(self):
        """An expired, not-yet-archived URL is marked archived and deactivated."""
        url_obj = Url.objects.create(
            original_url="https://www.example.com", short_url="exp001", owner_id=1,
            owner_email="alice@example.com", expires_at=timezone.now() - timedelta(days=1),
        )

        count = archive_expired_urls()

        url_obj.refresh_from_db()
        self.assertEqual(count, 1)
        self.assertTrue(url_obj.is_archived)
        self.assertFalse(url_obj.is_active)
        self.assertIsNotNone(url_obj.archived_at)

    def test_evicts_cache_for_archived_url(self):
        """An expired URL's cached lookup data is evicted so stale reads never resurface it."""
        url_obj = Url.objects.create(
            original_url="https://www.example.com", short_url="exp002", owner_id=1,
            owner_email="alice@example.com", expires_at=timezone.now() - timedelta(days=1),
        )
        cache_url(url_obj)
        self.assertIsNotNone(cache.get(cache_key("exp002")))

        archive_expired_urls()

        self.assertIsNone(cache.get(cache_key("exp002")))

    def test_ignores_non_expired_urls(self):
        """A URL with no expiry, or one still in the future, is left untouched."""
        no_expiry = Url.objects.create(
            original_url="https://www.example.com", short_url="exp003", owner_id=1, owner_email="alice@example.com",
        )
        future = Url.objects.create(
            original_url="https://www.example.com", short_url="exp004", owner_id=1,
            owner_email="alice@example.com", expires_at=timezone.now() + timedelta(days=1),
        )

        count = archive_expired_urls()

        self.assertEqual(count, 0)
        for url_obj in (no_expiry, future):
            url_obj.refresh_from_db()
            self.assertFalse(url_obj.is_archived)
            self.assertTrue(url_obj.is_active)

    def test_ignores_already_archived_urls(self):
        """A URL already archived isn't re-counted or re-touched."""
        url_obj = Url.objects.create(
            original_url="https://www.example.com", short_url="exp005", owner_id=1, owner_email="alice@example.com",
            expires_at=timezone.now() - timedelta(days=1), is_archived=True, is_active=False,
        )

        count = archive_expired_urls()

        self.assertEqual(count, 0)
        url_obj.refresh_from_db()
        self.assertIsNone(url_obj.archived_at)


class FetchUrlPreviewTaskTest(TestCase):
    """Tests the async task that fills in title/description/favicon from url-preview after a Url is created."""

    def setUp(self):
        self.url_obj = Url.objects.create(
            original_url="https://www.example.com", short_url="prev001",
            owner_id=1, owner_email="alice@example.com",
        )

    @patch('url_shortener.tasks.preview_client.fetch_preview')
    def test_fills_in_blank_fields_from_the_preview(self, mock_fetch_preview):
        mock_fetch_preview.return_value = {
            "title": "Example Domain", "description": "An example page", "favicon": "https://www.example.com/favicon.ico",
        }

        fetch_url_preview_task(self.url_obj.id)

        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.title, "Example Domain")
        self.assertEqual(self.url_obj.description, "An example page")
        self.assertEqual(self.url_obj.favicon, "https://www.example.com/favicon.ico")

    @patch('url_shortener.tasks.preview_client.fetch_preview')
    def test_never_overwrites_an_owner_supplied_value(self, mock_fetch_preview):
        self.url_obj.title = "My own title"
        self.url_obj.save()
        mock_fetch_preview.return_value = {
            "title": "Example Domain", "description": "An example page", "favicon": "https://www.example.com/favicon.ico",
        }

        fetch_url_preview_task(self.url_obj.id)

        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.title, "My own title")
        self.assertEqual(self.url_obj.description, "An example page")

    @patch('url_shortener.tasks.preview_client.fetch_preview')
    def test_does_nothing_when_url_preview_returns_none(self, mock_fetch_preview):
        mock_fetch_preview.return_value = None

        fetch_url_preview_task(self.url_obj.id)

        self.url_obj.refresh_from_db()
        self.assertIsNone(self.url_obj.title)
        self.assertIsNone(self.url_obj.description)
        self.assertIsNone(self.url_obj.favicon)

    @patch('url_shortener.tasks.preview_client.fetch_preview')
    def test_silently_does_nothing_if_the_url_was_since_deleted(self, mock_fetch_preview):
        deleted_id = self.url_obj.id
        self.url_obj.delete()

        fetch_url_preview_task(deleted_id)  # must not raise

        mock_fetch_preview.assert_not_called()
