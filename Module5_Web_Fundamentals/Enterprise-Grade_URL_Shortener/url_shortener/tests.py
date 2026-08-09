from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Url
from .services import UrlShortenerService


class UrlModelTest(TestCase): 
    def test_create_url(self):
        url = Url.objects.create(
            original_url="https://www.example.com",
            short_url="abc123"
        )
        self.assertEqual(url.original_url, "https://www.example.com")
        self.assertEqual(url.short_url, "abc123")


class UrlShortenerServiceTest(TestCase):
    def test_generate_short_code(self):
        code = UrlShortenerService.generate_short_code()
        self.assertEqual(len(code), 6)
    
    def test_create_short_url(self):
        url_obj = UrlShortenerService.create_short_url("https://www.google.com")
        self.assertEqual(url_obj.original_url, "https://www.google.com")
        self.assertEqual(len(url_obj.short_url), 6)


class CreateShortUrlAPITest(APITestCase):
    def test_create_success(self):
        data = {'original_url': 'https://www.example.com'}
        response = self.client.post(reverse('create-short-url'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('short_url', response.data)
        self.assertIn('short_link', response.data)
    
    def test_invalid_url(self):
        data = {'original_url': 'not-a-valid-url'}
        response = self.client.post(reverse('create-short-url'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RedirectUrlAPITest(APITestCase):
    def test_redirect_success(self):
        url_obj = Url.objects.create(
            original_url="https://www.example.com",
            short_url="test123"
        )
        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'test123'}))
        
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "https://www.example.com")
    
    def test_redirect_not_found(self):
        response = self.client.get(reverse('redirect-url', kwargs={'short_code': 'invalid'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


