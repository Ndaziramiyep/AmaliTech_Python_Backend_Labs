from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from analytics.models import ClickEvent

INTERNAL_KEY = "test-internal-key"


@override_settings(INTERNAL_API_KEY=INTERNAL_KEY)
class RecordClickAPITest(APITestCase):
    def test_record_click_requires_internal_key(self):
        data = {'short_code': 'abc123', 'owner_id': 1}
        response = self.client.post(reverse('record-click'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ClickEvent.objects.count(), 0)

    def test_record_click_rejects_wrong_internal_key(self):
        data = {'short_code': 'abc123', 'owner_id': 1}
        response = self.client.post(
            reverse('record-click'), data, format='json', HTTP_X_INTERNAL_KEY='wrong-key'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_record_click_success(self):
        data = {
            'short_code': 'abc123',
            'owner_id': 1,
            'referrer': 'https://google.com',
            'user_agent': 'pytest',
            'ip_address': '127.0.0.1',
        }
        response = self.client.post(
            reverse('record-click'), data, format='json', HTTP_X_INTERNAL_KEY=INTERNAL_KEY
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ClickEvent.objects.count(), 1)
        event = ClickEvent.objects.first()
        self.assertEqual(event.short_code, 'abc123')
        self.assertEqual(event.owner_id, 1)


class UrlClickStatsAPITest(APITestCase):
    def test_stats_require_owner_id(self):
        response = self.client.get(reverse('url-click-stats', kwargs={'short_code': 'abc123'}))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stats_with_no_clicks(self):
        response = self.client.get(
            reverse('url-click-stats', kwargs={'short_code': 'abc123'}), {'owner_id': 1}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['click_count'], 0)
        self.assertIsNone(response.data['last_clicked_at'])

    def test_stats_counts_only_own_clicks(self):
        ClickEvent.objects.create(short_code='abc123', owner_id=1)
        ClickEvent.objects.create(short_code='abc123', owner_id=1)
        ClickEvent.objects.create(short_code='abc123', owner_id=2)  # someone else's click on same code

        response = self.client.get(
            reverse('url-click-stats', kwargs={'short_code': 'abc123'}), {'owner_id': 1}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['click_count'], 2)
        self.assertIsNotNone(response.data['last_clicked_at'])


class UserClickSummaryAPITest(APITestCase):
    def test_summary_requires_owner_id(self):
        response = self.client.get(reverse('user-click-summary'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_summary_groups_by_short_code(self):
        ClickEvent.objects.create(short_code='abc123', owner_id=1)
        ClickEvent.objects.create(short_code='abc123', owner_id=1)
        ClickEvent.objects.create(short_code='xyz789', owner_id=1)
        ClickEvent.objects.create(short_code='abc123', owner_id=2)  # different owner, excluded

        response = self.client.get(reverse('user-click-summary'), {'owner_id': 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_code = {row['short_code']: row['click_count'] for row in response.data}
        self.assertEqual(by_code, {'abc123': 2, 'xyz789': 1})
