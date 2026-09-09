from django.test import TestCase

from analytics.models import ClickEvent
from analytics.tasks import track_click_task


class TrackClickTaskTest(TestCase):
    """Tests the write-behind task that persists a click event off the request path."""

    def test_creates_click_event_from_given_fields(self):
        """Calling the task directly creates a matching ClickEvent."""
        track_click_task(
            short_code='abc123', owner_id=1, referrer='https://google.com',
            user_agent='pytest', ip_address='127.0.0.1', city='Kigali', country='Rwanda',
        )

        self.assertEqual(ClickEvent.objects.count(), 1)
        event = ClickEvent.objects.first()
        self.assertEqual(event.short_code, 'abc123')
        self.assertEqual(event.owner_id, 1)
        self.assertEqual(event.city, 'Kigali')
        self.assertEqual(event.country, 'Rwanda')

    def test_defaults_optional_fields(self):
        """Calling the task with only the required fields persists sane defaults for the rest."""
        track_click_task(short_code='abc123', owner_id=1)

        event = ClickEvent.objects.first()
        self.assertEqual(event.referrer, '')
        self.assertEqual(event.user_agent, '')
        self.assertIsNone(event.ip_address)
        self.assertIsNone(event.city)
        self.assertIsNone(event.country)
