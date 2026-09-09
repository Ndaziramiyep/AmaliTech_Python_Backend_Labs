from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from url_shortener.caching import cache_key, cache_url
from url_shortener.models import Url
from url_shortener.tasks import (
    archive_expired_urls,
    delete_click_events_task,
    fetch_url_preview_task,
    record_click_task,
)


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


class RecordClickTaskTest(TestCase):
    """Tests the Celery task that decouples click reporting from the redirect request."""

    @patch('url_shortener.tasks.analytics_client.record_click')
    def test_delegates_to_analytics_client(self, mock_record_click):
        record_click_task(
            short_code='abc123', owner_id=1, referrer='https://example.com', user_agent='pytest', ip_address='1.2.3.4',
        )

        mock_record_click.assert_called_once_with(
            short_code='abc123', owner_id=1, referrer='https://example.com', user_agent='pytest', ip_address='1.2.3.4',
        )


class DeleteClickEventsTaskTest(TestCase):
    """Tests the Celery task that decouples the cascade-delete from the URL-delete request."""

    @patch('url_shortener.tasks.analytics_client.delete_click_events')
    def test_delegates_to_analytics_client(self, mock_delete_click_events):
        delete_click_events_task(['abc123', 'def456'])

        mock_delete_click_events.assert_called_once_with(['abc123', 'def456'])


class FetchUrlPreviewTaskTest(TestCase):
    """Tests the Celery task that decouples the destination-page preview fetch from URL creation."""

    def setUp(self):
        self.url_obj = Url.objects.create(
            original_url="https://www.example.com", short_url="prev01", owner_id=1, owner_email="alice@example.com",
        )

    @patch('url_shortener.tasks.preview_client.fetch_preview')
    def test_fills_in_blank_fields_from_the_fetched_preview(self, mock_fetch_preview):
        mock_fetch_preview.return_value = {
            "title": "Example Domain", "description": "An example.", "favicon": "https://www.example.com/favicon.ico",
        }

        fetch_url_preview_task(self.url_obj.id)

        mock_fetch_preview.assert_called_once_with("https://www.example.com")
        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.title, "Example Domain")
        self.assertEqual(self.url_obj.description, "An example.")
        self.assertEqual(self.url_obj.favicon, "https://www.example.com/favicon.ico")

    @patch('url_shortener.tasks.preview_client.fetch_preview')
    def test_does_not_overwrite_an_owner_supplied_title(self, mock_fetch_preview):
        self.url_obj.title = "My own title"
        self.url_obj.save()
        mock_fetch_preview.return_value = {
            "title": "Example Domain", "description": "An example.", "favicon": "https://www.example.com/favicon.ico",
        }

        fetch_url_preview_task(self.url_obj.id)

        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.title, "My own title")
        self.assertEqual(self.url_obj.description, "An example.")

    @patch('url_shortener.tasks.preview_client.fetch_preview')
    def test_does_nothing_if_the_url_was_since_deleted(self, mock_fetch_preview):
        deleted_id = self.url_obj.id
        self.url_obj.delete()

        fetch_url_preview_task(deleted_id)

        mock_fetch_preview.assert_not_called()
