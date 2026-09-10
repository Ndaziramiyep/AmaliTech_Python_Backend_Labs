from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from url_shortener.caching import cache_key, cache_url
from url_shortener.models import Url
from url_shortener.tasks import archive_expired_urls


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
