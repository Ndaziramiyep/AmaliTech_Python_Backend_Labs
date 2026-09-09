from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from analytics.models import ClickEvent

INTERNAL_KEY = "test-internal-key"


def make_access_token(user_id, email, is_staff=False, tier="Free"):
    """Mint a token the same way auth-service would, signed with this service's configured SIGNING_KEY."""
    token = AccessToken()
    token['user_id'] = str(user_id)  # matches auth-service's real (string) claim type
    token['email'] = email
    token['is_staff'] = is_staff
    token['tier'] = tier
    return str(token)


@override_settings(INTERNAL_API_KEY=INTERNAL_KEY)
class RecordClickAPITest(APITestCase):
    """Tests for the internal click-recording endpoint."""

    def test_record_click_requires_internal_key(self):
        """Recording a click without the internal key header returns a 401."""
        # No X-Internal-Key and no bearer token: DRF's permission_denied()
        # prefers 401 over 403 whenever a registered authenticator (our
        # StatelessJWTAuthentication) exposes a WWW-Authenticate header and
        # nothing authenticated the request, regardless of which permission
        # class actually failed.
        data = {'short_code': 'abc123', 'owner_id': 1}
        response = self.client.post(reverse('record-click'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(ClickEvent.objects.count(), 0)

    def test_record_click_rejects_wrong_internal_key(self):
        """Recording a click with an incorrect internal key returns a 401."""
        data = {'short_code': 'abc123', 'owner_id': 1}
        response = self.client.post(
            reverse('record-click'), data, format='json', HTTP_X_INTERNAL_KEY='wrong-key'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_record_click_success(self):
        """Recording a click with a valid internal key persists a ClickEvent and returns 201."""
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

    def test_record_click_accepts_optional_geo_fields(self):
        """Recording a click with city/country persists them on the ClickEvent."""
        data = {'short_code': 'abc123', 'owner_id': 1, 'city': 'Kigali', 'country': 'Rwanda'}
        response = self.client.post(
            reverse('record-click'), data, format='json', HTTP_X_INTERNAL_KEY=INTERNAL_KEY
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = ClickEvent.objects.first()
        self.assertEqual(event.city, 'Kigali')
        self.assertEqual(event.country, 'Rwanda')

    def test_record_click_accepts_long_short_code(self):
        """Recording a click for a custom_alias-length short_code (up to 50 chars) succeeds."""
        long_code = 'a' * 50
        data = {'short_code': long_code, 'owner_id': 1}
        response = self.client.post(
            reverse('record-click'), data, format='json', HTTP_X_INTERNAL_KEY=INTERNAL_KEY
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ClickEvent.objects.first().short_code, long_code)

    def test_delete_cascades_click_history_for_given_codes(self):
        """Deleting with a list of short_codes removes every matching ClickEvent, and only those."""
        ClickEvent.objects.create(short_code='abc123', owner_id=1)
        ClickEvent.objects.create(short_code='my-alias', owner_id=1)
        ClickEvent.objects.create(short_code='untouched', owner_id=1)

        response = self.client.delete(
            reverse('record-click'), {'short_codes': ['abc123', 'my-alias']},
            format='json', HTTP_X_INTERNAL_KEY=INTERNAL_KEY,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ClickEvent.objects.count(), 1)
        self.assertTrue(ClickEvent.objects.filter(short_code='untouched').exists())

    def test_delete_requires_internal_key(self):
        """Cascade-deleting click history without the internal key returns a 401."""
        response = self.client.delete(reverse('record-click'), {'short_codes': ['abc123']}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UrlClickStatsAPITest(APITestCase):
    """Tests for the per-short-code click stats endpoint."""

    def setUp(self):
        """Authenticate the test client as a stub user via a signed JWT."""
        self.access_token = make_access_token(user_id=1, email="alice@example.com")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_stats_require_authentication(self):
        """Fetching stats without credentials returns a 401."""
        self.client.credentials()
        response = self.client.get(reverse('url-click-stats', kwargs={'short_code': 'abc123'}))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_stats_with_no_clicks(self):
        """A short code with no recorded clicks reports a zero count and a null timestamp."""
        response = self.client.get(reverse('url-click-stats', kwargs={'short_code': 'abc123'}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['click_count'], 0)
        self.assertIsNone(response.data['last_clicked_at'])

    def test_stats_counts_only_own_clicks(self):
        """Click stats for a short code only count clicks owned by the requesting user."""
        ClickEvent.objects.create(short_code='abc123', owner_id=1)
        ClickEvent.objects.create(short_code='abc123', owner_id=1)
        ClickEvent.objects.create(short_code='abc123', owner_id=2)  # someone else's click on same code

        response = self.client.get(reverse('url-click-stats', kwargs={'short_code': 'abc123'}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['click_count'], 2)
        self.assertIsNotNone(response.data['last_clicked_at'])


class UserClickSummaryAPITest(APITestCase):
    """Tests for the per-user click summary endpoint."""

    def setUp(self):
        """Authenticate the test client as a stub user via a signed JWT."""
        self.access_token = make_access_token(user_id=1, email="alice@example.com")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_summary_groups_by_short_code(self):
        """The click summary groups counts by short code and excludes other owners' clicks."""
        ClickEvent.objects.create(short_code='abc123', owner_id=1)
        ClickEvent.objects.create(short_code='abc123', owner_id=1)
        ClickEvent.objects.create(short_code='xyz789', owner_id=1)
        ClickEvent.objects.create(short_code='abc123', owner_id=2)  # different owner, excluded

        response = self.client.get(reverse('user-click-summary'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_code = {row['short_code']: row['click_count'] for row in response.data}
        self.assertEqual(by_code, {'abc123': 2, 'xyz789': 1})


class DetailedAnalyticsAPITest(APITestCase):
    """Tests for the Premium/Admin-only time-series + geo-location analytics endpoint."""

    def setUp(self):
        """Create a mix of click events across days and locations for short code 'abc123' owned by user 1."""
        ClickEvent.objects.create(short_code='abc123', owner_id=1, city='Kigali', country='Rwanda')
        ClickEvent.objects.create(short_code='abc123', owner_id=1, city='Kigali', country='Rwanda')
        ClickEvent.objects.create(short_code='abc123', owner_id=1, city=None, country=None)
        ClickEvent.objects.create(short_code='abc123', owner_id=2)  # different owner, excluded for non-admin

    def authenticate(self, token):
        """Attach the given access token as a Bearer credential on the client."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_requires_authentication(self):
        """Fetching detailed analytics without credentials returns a 401."""
        response = self.client.get(reverse('detailed-analytics', kwargs={'short_code': 'abc123'}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_free_tier_forbidden(self):
        """A Free-tier user gets a 403, not the analytics payload."""
        self.authenticate(make_access_token(user_id=1, email="alice@example.com", tier="Free"))
        response = self.client.get(reverse('detailed-analytics', kwargs={'short_code': 'abc123'}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_premium_tier_gets_time_series_and_geo_breakdown(self):
        """A Premium-tier owner gets their own click_count, time series, and geo breakdown."""
        self.authenticate(make_access_token(user_id=1, email="alice@example.com", tier="Premium"))
        response = self.client.get(reverse('detailed-analytics', kwargs={'short_code': 'abc123'}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['click_count'], 3)  # excludes owner_id=2's click
        self.assertEqual(len(response.data['time_series']), 1)
        self.assertEqual(response.data['time_series'][0]['count'], 3)
        geo_counts = {(row['city'], row['country']): row['count'] for row in response.data['geo_breakdown']}
        self.assertEqual(geo_counts, {('Kigali', 'Rwanda'): 2, (None, None): 1})

    def test_admin_sees_all_owners_clicks(self):
        """A staff/admin user's detailed analytics includes every owner's clicks for that code."""
        self.authenticate(make_access_token(user_id=99, email="admin@example.com", is_staff=True))
        response = self.client.get(reverse('detailed-analytics', kwargs={'short_code': 'abc123'}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['click_count'], 4)  # includes owner_id=2's click too
