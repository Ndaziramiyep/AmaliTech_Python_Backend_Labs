from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegisterAPITest(APITestCase):
    def test_register_success(self):
        data = {
            'email': 'alice@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'StrongPass123',
        }
        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['tier'], User.Tier.FREE)
        self.assertTrue(User.objects.filter(email='alice@example.com').exists())

    def test_register_duplicate_email(self):
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
        data = {
            'email': 'alice@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'DifferentPass123',
        }
        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        data = {
            'email': 'alice@example.com',
            'password': 'short',
            'confirm_password': 'short',
        }
        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='alice@example.com', email='alice@example.com', password='StrongPass123'
        )

    def test_login_success(self):
        data = {'email': 'alice@example.com', 'password': 'StrongPass123'}
        response = self.client.post(reverse('login'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        data = {'email': 'alice@example.com', 'password': 'wrong-password'}
        response = self.client.post(reverse('login'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
