from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class HealthCheckTest(TestCase):
    """Tests the /health/ endpoint's database and Redis connectivity checks."""

    def test_healthy_when_database_and_redis_reachable(self):
        """Returns 200 with both checks true when the database and Redis both respond."""
        response = self.client.get(reverse('health'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "checks": {"database": True, "redis": True}})

    @patch('url_shortener.health._check_redis', return_value=False)
    def test_unavailable_when_redis_unreachable(self, mock_check_redis):
        """Returns 503 with redis: false when Redis can't be reached."""
        response = self.client.get(reverse('health'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable", "checks": {"database": True, "redis": False}})

    @patch('url_shortener.health._check_database', return_value=False)
    def test_unavailable_when_database_unreachable(self, mock_check_database):
        """Returns 503 with database: false when the database can't be reached."""
        response = self.client.get(reverse('health'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable", "checks": {"database": False, "redis": True}})
