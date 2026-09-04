import threading
from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from url_shortener.models import Tag, Url


def make_access_token(user_id, email, is_staff=False, tier="Free"):
    """Mint a token the same way auth-service would, simulating a real cross-service token."""
    token = AccessToken()
    token['user_id'] = str(user_id)  # matches auth-service's real (string) claim type
    token['email'] = email
    token['is_staff'] = is_staff
    token['tier'] = tier
    return str(token)


def _call_and_join_threads(callable_):
    """Calls callable_(), then joins any background threads it spawned, making fire-and-forget side effects deterministic in tests."""
    before = set(threading.enumerate())
    result = callable_()
    for thread in set(threading.enumerate()) - before:
        thread.join(timeout=2)
    return result


class UrlListCreateAPITest(APITestCase):
    """Tests the list/create endpoint's authentication, validation, pagination, tag search, and per-owner scoping."""

    def setUp(self):
        """Mint an access token for a test user before each test."""
        self.access_token = make_access_token(user_id=1, email="alice@example.com")

    def authenticate(self, token=None):
        """Attach a Bearer credential (the test user's by default) on the client."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token or self.access_token}")

    def test_create_requires_authentication(self):
        """Assert that creating a short URL without credentials returns 401."""
        data = {'original_url': 'https://www.example.com'}
        response = self.client.post(reverse('list-create-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_success(self):
        """Assert that an authenticated request creates a short URL and returns its details."""
        self.authenticate()
        data = {'original_url': 'https://www.example.com'}
        response = self.client.post(reverse('list-create-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('short_url', response.data)
        self.assertIn('short_link', response.data)
        self.assertEqual(response.data['owner'], 'alice@example.com')

    def test_invalid_url(self):
        """Assert that submitting a malformed URL returns a 400 validation error."""
        self.authenticate()
        data = {'original_url': 'not-a-valid-url'}
        response = self.client.post(reverse('list-create-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_requires_authentication(self):
        """Assert that listing URLs without credentials returns 401."""
        response = self.client.get(reverse('list-create-url'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_only_returns_own_urls_for_normal_user(self):
        """Assert that a normal user's list only includes URLs they own, not other users'."""
        Url.objects.create(original_url="https://mine.example.com", short_url="mine01", owner_id=1, owner_email="alice@example.com")
        Url.objects.create(original_url="https://theirs.example.com", short_url="theirs1", owner_id=2, owner_email="bob@example.com")
        self.authenticate()

        response = self.client.get(reverse('list-create-url'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        short_urls = [item['short_url'] for item in response.data['results']]
        self.assertEqual(short_urls, ['mine01'])

    def test_list_returns_all_urls_for_admin(self):
        """Assert that a staff/admin user's list includes every owner's URLs."""
        Url.objects.create(original_url="https://mine.example.com", short_url="mine01", owner_id=1, owner_email="alice@example.com")
        Url.objects.create(original_url="https://theirs.example.com", short_url="theirs1", owner_id=2, owner_email="bob@example.com")
        admin_token = make_access_token(user_id=99, email="admin@example.com", is_staff=True)
        self.authenticate(admin_token)

        response = self.client.get(reverse('list-create-url'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        short_urls = {item['short_url'] for item in response.data['results']}
        self.assertEqual(short_urls, {'mine01', 'theirs1'})

    def test_list_response_is_paginated(self):
        """Assert that the list response is a paginated envelope with count/next/previous/results."""
        Url.objects.create(original_url="https://mine.example.com", short_url="mine01", owner_id=1, owner_email="alice@example.com")
        self.authenticate()

        response = self.client.get(reverse('list-create-url'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ('count', 'next', 'previous', 'results'):
            self.assertIn(key, response.data)
        self.assertEqual(response.data['count'], 1)

    def test_list_filters_by_tag(self):
        """Assert that ?tag= only returns URLs carrying that exact tag."""
        tagged = Url.objects.create(original_url="https://tagged.example.com", short_url="tagged1", owner_id=1, owner_email="alice@example.com")
        tagged.tags.set([Tag.objects.create(name="news")])
        Url.objects.create(original_url="https://untagged.example.com", short_url="untag01", owner_id=1, owner_email="alice@example.com")
        self.authenticate()

        response = self.client.get(reverse('list-create-url'), {'tag': 'news'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        short_urls = [item['short_url'] for item in response.data['results']]
        self.assertEqual(short_urls, ['tagged1'])

    def test_free_tier_cannot_set_custom_alias(self):
        """Assert that a Free-tier user's custom_alias is rejected with a 400."""
        self.authenticate()
        data = {'original_url': 'https://www.example.com', 'custom_alias': 'my-alias'}
        response = self.client.post(reverse('list-create-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Url.objects.filter(custom_alias='my-alias').exists())

    def test_premium_tier_can_set_custom_alias(self):
        """Assert that a Premium-tier user's custom_alias is accepted and resolvable."""
        self.authenticate(make_access_token(user_id=1, email="alice@example.com", tier="Premium"))
        data = {'original_url': 'https://www.example.com', 'custom_alias': 'my-alias'}
        response = self.client.post(reverse('list-create-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['custom_alias'], 'my-alias')

    def test_duplicate_custom_alias_rejected(self):
        """Assert that a custom_alias already used by another URL is rejected with a 400."""
        Url.objects.create(original_url="https://existing.example.com", short_url="exist1", custom_alias="taken", owner_id=5, owner_email="dave@example.com")
        self.authenticate(make_access_token(user_id=1, email="alice@example.com", tier="Premium"))
        data = {'original_url': 'https://www.example.com', 'custom_alias': 'taken'}
        response = self.client.post(reverse('list-create-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_tags(self):
        """Assert that submitted tag names are created and attached to the new URL."""
        self.authenticate()
        data = {'original_url': 'https://www.example.com', 'tags': ['news', 'tech']}
        response = self.client.post(reverse('list-create-url'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data['tags']), {'news', 'tech'})
        self.assertEqual(Tag.objects.count(), 2)

    def test_create_rate_limited_when_tier_quota_exceeded(self):
        """Assert that exceeding the caller's tiered rate limit returns a 429."""
        self.authenticate()
        with patch('url_shortener.api.throttling.TIER_RATES', {'Free': '1/day', 'Premium': '1000/day', 'Admin': '1000/day'}):
            first = self.client.post(reverse('list-create-url'), {'original_url': 'https://one.example.com'}, format='json')
            second = self.client.post(reverse('list-create-url'), {'original_url': 'https://two.example.com'}, format='json')

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_free_tier_capped_at_ten_active_urls(self):
        """Assert that a Free-tier user's 11th active URL is rejected with a 403."""
        self.authenticate()
        for i in range(10):
            Url.objects.create(original_url=f"https://existing{i}.example.com", short_url=f"exist{i:02d}", owner_id=1, owner_email="alice@example.com")

        response = self.client.post(reverse('list-create-url'), {'original_url': 'https://eleventh.example.com'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_free_tier_cap_ignores_inactive_urls(self):
        """Assert that deactivated URLs don't count toward the Free-tier active-URL cap."""
        self.authenticate()
        for i in range(10):
            Url.objects.create(
                original_url=f"https://existing{i}.example.com", short_url=f"exist{i:02d}",
                owner_id=1, owner_email="alice@example.com", is_active=False,
            )

        response = self.client.post(reverse('list-create-url'), {'original_url': 'https://eleventh.example.com'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_premium_tier_not_capped(self):
        """Assert that a Premium-tier user can exceed 10 active URLs."""
        self.authenticate(make_access_token(user_id=1, email="alice@example.com", tier="Premium"))
        for i in range(10):
            Url.objects.create(original_url=f"https://existing{i}.example.com", short_url=f"exist{i:02d}", owner_id=1, owner_email="alice@example.com")

        response = self.client.post(reverse('list-create-url'), {'original_url': 'https://eleventh.example.com'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class UrlDetailAPITest(APITestCase):
    """Tests the detail endpoint's public read (full details), and owner/admin-only PUT/PATCH/DELETE."""

    def setUp(self):
        """Clear the shared cache (it isn't rolled back between tests like the DB is) and create a fixture owned by user id 2."""
        cache.clear()
        self.url_obj = Url.objects.create(
            original_url="https://www.example.com",
            short_url="test123",
            owner_id=2,
            owner_email="bob@example.com",
        )

    def authenticate(self, token):
        """Attach the given access token as a Bearer credential on the client."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_get_is_public_and_returns_full_details(self):
        """Assert that retrieving a short code requires no authentication and returns the full representation."""
        response = self.client.get(reverse('url-detail', kwargs={'short_code': 'test123'}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['original_url'], "https://www.example.com")
        self.assertEqual(response.data['owner'], "bob@example.com")
        self.assertIn('click_count', response.data)
        self.assertIn('tags', response.data)

    def test_update_requires_authentication(self):
        """Assert that updating a short code without credentials returns 401."""
        response = self.client.patch(
            reverse('url-detail', kwargs={'short_code': 'test123'}),
            {'original_url': 'https://updated.example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_update_via_patch(self):
        """Assert that the URL's own owner can partially update its destination via PATCH."""
        self.authenticate(make_access_token(user_id=2, email="bob@example.com"))

        response = self.client.patch(
            reverse('url-detail', kwargs={'short_code': 'test123'}),
            {'original_url': 'https://updated.example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.original_url, "https://updated.example.com")

    def test_owner_can_update_via_put(self):
        """Assert that the URL's own owner can fully update it via PUT."""
        self.authenticate(make_access_token(user_id=2, email="bob@example.com"))

        response = self.client.put(
            reverse('url-detail', kwargs={'short_code': 'test123'}),
            {'original_url': 'https://put-updated.example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.original_url, "https://put-updated.example.com")

    def test_put_requires_original_url(self):
        """Assert that PUT without original_url (a full update) returns a 400."""
        self.authenticate(make_access_token(user_id=2, email="bob@example.com"))

        response = self.client.put(
            reverse('url-detail', kwargs={'short_code': 'test123'}),
            {'title': 'New Title'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_cannot_update(self):
        """Assert that a normal user other than the owner is forbidden from updating it."""
        self.authenticate(make_access_token(user_id=3, email="carol@example.com"))

        response = self.client.patch(
            reverse('url-detail', kwargs={'short_code': 'test123'}),
            {'original_url': 'https://updated.example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.original_url, "https://www.example.com")

    def test_admin_can_update_another_users_url(self):
        """Assert that a staff/admin user can update a URL they don't own."""
        self.authenticate(make_access_token(user_id=99, email="admin@example.com", is_staff=True))

        response = self.client.patch(
            reverse('url-detail', kwargs={'short_code': 'test123'}),
            {'original_url': 'https://updated.example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.original_url, "https://updated.example.com")

    def test_delete_requires_authentication(self):
        """Assert that deleting a short code without credentials returns 401."""
        response = self.client.delete(reverse('url-detail', kwargs={'short_code': 'test123'}))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_other_user_cannot_delete(self):
        """Assert that a normal user other than the owner is forbidden from deleting it."""
        self.authenticate(make_access_token(user_id=3, email="carol@example.com"))

        response = self.client.delete(reverse('url-detail', kwargs={'short_code': 'test123'}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Url.objects.filter(short_url='test123').exists())

    def test_owner_can_delete(self):
        """Assert that the URL's own owner can delete it."""
        self.authenticate(make_access_token(user_id=2, email="bob@example.com"))

        response = self.client.delete(reverse('url-detail', kwargs={'short_code': 'test123'}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Url.objects.filter(short_url='test123').exists())

    @patch('url_shortener.api.views.analytics_client.delete_click_events')
    def test_delete_cascades_to_analytics_service(self, mock_delete_click_events):
        """Assert that deleting a URL fire-and-forgets a cascade-delete of its click history."""
        self.authenticate(make_access_token(user_id=2, email="bob@example.com"))

        _call_and_join_threads(lambda: self.client.delete(reverse('url-detail', kwargs={'short_code': 'test123'})))

        mock_delete_click_events.assert_called_once_with(['test123'])

    def test_admin_can_delete_another_users_url(self):
        """Assert that a staff/admin user can delete a URL they don't own."""
        self.authenticate(make_access_token(user_id=99, email="admin@example.com", is_staff=True))

        response = self.client.delete(reverse('url-detail', kwargs={'short_code': 'test123'}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Url.objects.filter(short_url='test123').exists())

    def test_get_by_custom_alias(self):
        """Assert that a URL with a custom_alias also resolves by that alias."""
        self.url_obj.custom_alias = "bobs-link"
        self.url_obj.save()

        response = self.client.get(reverse('url-detail', kwargs={'short_code': 'bobs-link'}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['original_url'], "https://www.example.com")

    def test_inactive_url_not_found(self):
        """Assert that a deactivated URL resolves as 404, not 200."""
        self.url_obj.is_active = False
        self.url_obj.save()

        response = self.client.get(reverse('url-detail', kwargs={'short_code': 'test123'}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_expired_url_not_found(self):
        """Assert that a URL past its expires_at resolves as 404, not 200."""
        self.url_obj.expires_at = timezone.now() - timedelta(days=1)
        self.url_obj.save()

        response = self.client.get(reverse('url-detail', kwargs={'short_code': 'test123'}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_deactivate_via_patch(self):
        """Assert that the owner can deactivate their URL via PATCH, taking it out of resolution."""
        self.authenticate(make_access_token(user_id=2, email="bob@example.com"))

        response = self.client.patch(
            reverse('url-detail', kwargs={'short_code': 'test123'}),
            {'is_active': False},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.url_obj.refresh_from_db()
        self.assertFalse(self.url_obj.is_active)


class RedirectUrlAPITest(APITestCase):
    """Tests the redirect endpoint's success and not-found behavior."""

    def setUp(self):
        """Clear the shared cache (it isn't rolled back between tests like the DB is) and create a fixture to redirect against."""
        cache.clear()
        self.url_obj = Url.objects.create(
            original_url="https://www.example.com",
            short_url="test123",
            owner_id=2,
            owner_email="bob@example.com",
        )

    @patch('url_shortener.api.views.analytics_client.record_click')
    def test_redirect_success(self, mock_record_click):
        """Assert that resolving a known short code redirects and records a click event in the background."""
        response = _call_and_join_threads(
            lambda: self.client.get(reverse('redirect-url', kwargs={'short_code': 'test123'}))
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "https://www.example.com")
        mock_record_click.assert_called_once()
        self.assertEqual(mock_record_click.call_args.kwargs['short_code'], 'test123')
        self.assertEqual(mock_record_click.call_args.kwargs['owner_id'], 2)

    def test_redirect_not_found(self):
        """Assert that resolving an unknown short code returns 404."""
        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'invalid'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('url_shortener.api.views.analytics_client.record_click')
    def test_redirect_increments_click_count(self, mock_record_click):
        """Assert that each successful redirect atomically increments the Url's click_count."""
        self.client.get(reverse('redirect-url', kwargs={'short_code': 'test123'}))
        self.client.get(reverse('redirect-url', kwargs={'short_code': 'test123'}))

        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.click_count, 2)

    def test_redirect_not_found_when_expired(self):
        """Assert that a redirect for an expired URL returns 404, not a stale 302."""
        self.url_obj.expires_at = timezone.now() - timedelta(days=1)
        self.url_obj.save()

        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'test123'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
