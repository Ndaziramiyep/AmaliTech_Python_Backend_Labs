from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from url_shortener.models import Click, Url

User = get_user_model()


class AuthenticatedAPITestCase(APITestCase):
    def make_user(self, username, **extra):
        user = User.objects.create_user(username=username, email=f"{username}@example.com", password="pw", **extra)
        token = str(RefreshToken.for_user(user).access_token)
        return user, token

    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class CreateShortUrlAPITest(AuthenticatedAPITestCase):
    def setUp(self):
        self.user, self.token = self.make_user("alice")

    def test_create_requires_authentication(self):
        data = {'original_url': 'https://www.example.com'}
        response = self.client.post(reverse('url-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_success(self):
        self.authenticate(self.token)
        data = {'original_url': 'https://www.example.com', 'tags': ['Marketing']}
        response = self.client.post(reverse('url-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('short_code', response.data)
        self.assertIn('short_link', response.data)
        self.assertEqual(response.data['owner'], 'alice')
        self.assertEqual([t['name'] for t in response.data['tags']], ['Marketing'])

    def test_create_with_taken_alias(self):
        Url.objects.create(original_url='https://a.com', short_code='taken', owner=self.user)
        self.authenticate(self.token)
        data = {'original_url': 'https://www.example.com', 'custom_alias': 'taken'}
        response = self.client.post(reverse('url-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_url(self):
        self.authenticate(self.token)
        data = {'original_url': 'not-a-valid-url'}
        response = self.client.post(reverse('url-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_free_user_cannot_use_custom_alias(self):
        self.authenticate(self.token)
        data = {'original_url': 'https://www.example.com', 'custom_alias': 'mylink'}
        response = self.client.post(reverse('url-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_premium_user_can_use_custom_alias(self):
        premium, premium_token = self.make_user("carol", is_premium=True)
        self.authenticate(premium_token)
        data = {'original_url': 'https://www.example.com', 'custom_alias': 'mylink'}
        response = self.client.post(reverse('url-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['short_code'], 'mylink')

    def test_free_user_limited_to_ten_active_urls(self):
        self.authenticate(self.token)
        for _ in range(10):
            Url.objects.create(original_url='https://a.com', short_code=f'code{_:03d}', owner=self.user)

        data = {'original_url': 'https://www.example.com'}
        response = self.client.post(reverse('url-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_premium_user_not_limited_to_ten_active_urls(self):
        premium, premium_token = self.make_user("dave", is_premium=True)
        for i in range(10):
            Url.objects.create(original_url='https://a.com', short_code=f'pcod{i:03d}', owner=premium)

        self.authenticate(premium_token)
        data = {'original_url': 'https://www.example.com'}
        response = self.client.post(reverse('url-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ListUrlsAPITest(AuthenticatedAPITestCase):
    def test_list_only_returns_own_urls(self):
        alice, alice_token = self.make_user("alice")
        bob, _ = self.make_user("bob")
        Url.objects.create(original_url='https://a.com', short_code='alice01', owner=alice)
        Url.objects.create(original_url='https://b.com', short_code='bob0001', owner=bob)

        self.authenticate(alice_token)
        response = self.client.get(reverse('url-list-create'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codes = [item['short_code'] for item in response.data]
        self.assertEqual(codes, ['alice01'])


class UrlDetailAPITest(AuthenticatedAPITestCase):
    def setUp(self):
        self.owner, self.owner_token = self.make_user("alice")
        self.other, self.other_token = self.make_user("bob")
        self.url = Url.objects.create(original_url='https://a.com', short_code='mycode1', owner=self.owner)

    def test_owner_can_retrieve(self):
        self.authenticate(self.owner_token)
        response = self.client.get(reverse('url-detail', kwargs={'short_code': 'mycode1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_owner_cannot_retrieve(self):
        self.authenticate(self.other_token)
        response = self.client.get(reverse('url-detail', kwargs={'short_code': 'mycode1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_update(self):
        self.authenticate(self.owner_token)
        response = self.client.put(
            reverse('url-detail', kwargs={'short_code': 'mycode1'}),
            {'title': 'New title'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'New title')

    def test_owner_can_deactivate(self):
        self.authenticate(self.owner_token)
        response = self.client.delete(reverse('url-detail', kwargs={'short_code': 'mycode1'}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.url.refresh_from_db()
        self.assertFalse(self.url.is_active)


class RedirectUrlAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bob", email="bob@example.com", password="password123")

    def test_redirect_success_and_logs_click(self):
        Url.objects.create(
            original_url="https://www.example.com",
            short_code="test123",
            owner=self.user,
        )
        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'test123'}))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "https://www.example.com")

        url_obj = Url.objects.get(short_code='test123')
        self.assertEqual(url_obj.click_count, 1)
        self.assertEqual(Click.objects.filter(url=url_obj).count(), 1)

    def test_redirect_not_found(self):
        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'invalid'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_redirect_inactive_url_not_found(self):
        Url.objects.create(
            original_url="https://www.example.com", short_code="inact01", owner=self.user, is_active=False,
        )
        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'inact01'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AnalyticsAPITest(APITestCase):
    def setUp(self):
        self.free_user = User.objects.create_user(
            username="free", email="free@example.com", password="pw"
        )
        self.premium_user = User.objects.create_user(
            username="premium", email="premium@example.com", password="pw", is_premium=True,
        )
        self.url = Url.objects.create(
            original_url="https://a.com", short_code="an00001", owner=self.premium_user,
        )
        Click.objects.create(url=self.url, ip_address="1.1.1.1", country="US", user_agent="ua")
        Click.objects.create(url=self.url, ip_address="2.2.2.2", country="US", user_agent="ua")
        Click.objects.create(url=self.url, ip_address="3.3.3.3", country="KE", user_agent="ua")

    def authenticate_as(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_free_user_forbidden(self):
        free_owned = Url.objects.create(original_url="https://b.com", short_code="fr00001", owner=self.free_user)
        self.authenticate_as(self.free_user)
        response = self.client.get(reverse('url-analytics', kwargs={'short_code': free_owned.short_code}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_premium_user_gets_analytics(self):
        self.authenticate_as(self.premium_user)
        response = self.client.get(reverse('url-analytics', kwargs={'short_code': self.url.short_code}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        countries = {row['country']: row['count'] for row in response.data['clicks_by_country']}
        self.assertEqual(countries, {'US': 2, 'KE': 1})
