from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


class RegisterAPITest(APITestCase):
    """Tests the registration endpoint's success and validation-failure paths."""

    def test_register_success(self):
        """Registering with valid data creates a user and returns JWT tokens."""
        data = {
            'email': 'alice@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'StrongPass123',
        }
        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertTrue(User.objects.filter(email='alice@example.com').exists())

    def test_register_defaults_to_free_tier(self):
        """A newly registered user defaults to the Free tier and is_premium=False."""
        data = {
            'email': 'alice@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'StrongPass123',
        }
        self.client.post(reverse('register'), data, format='json')

        user = User.objects.get(email='alice@example.com')
        self.assertEqual(user.tier, User.TIER_FREE)
        self.assertFalse(user.is_premium)

    def test_register_duplicate_email(self):
        """Registering with an already-used email returns a 400."""
        User.objects.create_user(
            username='alice@example.com', email='alice@example.com', password='StrongPass123'
        )
        data = {
            'email': 'alice@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'StrongPass123',
        }
        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        """Registering with mismatched passwords returns a 400."""
        data = {
            'email': 'alice@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'DifferentPass123',
        }
        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        """Registering with a weak password returns a 400."""
        data = {
            'email': 'alice@example.com',
            'password': 'short',
            'confirm_password': 'short',
        }
        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginAPITest(APITestCase):
    """Tests the login endpoint's success and failure paths."""

    def setUp(self):
        """Clears the shared throttle cache (it isn't rolled back between tests like the DB is) and creates a user to log in against."""
        cache.clear()
        self.user = User.objects.create_user(
            username='alice@example.com', email='alice@example.com', password='StrongPass123'
        )

    def test_login_success(self):
        """Logging in with valid credentials returns JWT tokens."""
        data = {'email': 'alice@example.com', 'password': 'StrongPass123'}
        response = self.client.post(reverse('login'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_includes_email_claim(self):
        """The issued access token's payload includes the user's email claim."""
        import jwt

        data = {'email': 'alice@example.com', 'password': 'StrongPass123'}
        response = self.client.post(reverse('login'), data, format='json')

        payload = jwt.decode(response.data['access'], options={"verify_signature": False})
        self.assertEqual(payload['email'], 'alice@example.com')

    def test_login_includes_is_staff_claim(self):
        """The issued access token's payload includes the user's is_staff claim."""
        import jwt

        data = {'email': 'alice@example.com', 'password': 'StrongPass123'}
        response = self.client.post(reverse('login'), data, format='json')

        payload = jwt.decode(response.data['access'], options={"verify_signature": False})
        self.assertEqual(payload['is_staff'], False)

    def test_login_includes_is_staff_claim_for_staff_user(self):
        """A staff user's access token payload has is_staff set to True."""
        import jwt

        self.user.is_staff = True
        self.user.save(update_fields=['is_staff'])
        data = {'email': 'alice@example.com', 'password': 'StrongPass123'}
        response = self.client.post(reverse('login'), data, format='json')

        payload = jwt.decode(response.data['access'], options={"verify_signature": False})
        self.assertEqual(payload['is_staff'], True)

    def test_login_includes_tier_claim(self):
        """The issued access token's payload includes the user's tier claim."""
        import jwt

        data = {'email': 'alice@example.com', 'password': 'StrongPass123'}
        response = self.client.post(reverse('login'), data, format='json')

        payload = jwt.decode(response.data['access'], options={"verify_signature": False})
        self.assertEqual(payload['tier'], User.TIER_FREE)

    def test_login_includes_tier_claim_for_premium_user(self):
        """A Premium user's access token payload has the Premium tier claim."""
        import jwt

        self.user.tier = User.TIER_PREMIUM
        self.user.save()
        data = {'email': 'alice@example.com', 'password': 'StrongPass123'}
        response = self.client.post(reverse('login'), data, format='json')

        payload = jwt.decode(response.data['access'], options={"verify_signature": False})
        self.assertEqual(payload['tier'], User.TIER_PREMIUM)

    def test_admin_tier_grants_staff_status(self):
        """Setting a user's tier to Admin also grants them Django staff status."""
        self.user.tier = User.TIER_ADMIN
        self.user.save()

        self.assertTrue(self.user.is_staff)

    def test_login_invalid_credentials(self):
        """Logging in with the wrong password returns a 400."""
        data = {'email': 'alice@example.com', 'password': 'wrong-password'}
        response = self.client.post(reverse('login'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_rate_limited_after_five_attempts_per_minute(self):
        """The 6th login attempt within a minute from the same client returns a 429."""
        data = {'email': 'alice@example.com', 'password': 'wrong-password'}
        for _ in range(5):
            response = self.client.post(reverse('login'), data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
