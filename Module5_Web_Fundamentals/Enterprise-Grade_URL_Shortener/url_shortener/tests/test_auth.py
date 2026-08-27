from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class RegisterAPITest(APITestCase):
    def test_register_success(self):
        data = {'username': 'alice', 'password': 'password123'}
        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertTrue(User.objects.filter(username='alice').exists())

    def test_register_duplicate_username(self):
        User.objects.create_user(username='alice', password='password123')
        data = {'username': 'alice', 'password': 'password123'}
        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        data = {'username': 'alice', 'password': 'short'}
        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')

    def test_login_success(self):
        data = {'username': 'alice', 'password': 'password123'}
        response = self.client.post(reverse('login'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_invalid_credentials(self):
        data = {'username': 'alice', 'password': 'wrong-password'}
        response = self.client.post(reverse('login'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
