from django.test import TestCase
from django.urls import reverse


class HealthCheckTest(TestCase):
    """Tests GET /health/ — database connectivity is the only dependency this stateless service has."""

    def test_healthy_returns_200(self):
        response = self.client.get(reverse('health'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        self.assertTrue(response.json()['checks']['database'])
