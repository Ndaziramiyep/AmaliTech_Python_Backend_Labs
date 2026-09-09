from django.test import SimpleTestCase

from url_shortener.clients.resilience import CircuitBreaker


class CircuitBreakerTest(SimpleTestCase):
    """Unit tests for the CircuitBreaker shared by every client under url_shortener/clients/."""

    def test_closed_by_default(self):
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=30)
        self.assertFalse(breaker.is_open())

    def test_stays_closed_below_threshold(self):
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=30)
        breaker.record_failure()
        self.assertFalse(breaker.is_open())

    def test_opens_once_threshold_is_reached(self):
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=30)
        breaker.record_failure()
        breaker.record_failure()
        self.assertTrue(breaker.is_open())

    def test_success_resets_the_failure_count(self):
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=30)
        breaker.record_failure()
        breaker.record_success()
        breaker.record_failure()
        self.assertFalse(breaker.is_open())

    def test_half_opens_for_a_trial_call_once_recovery_timeout_elapses(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=0)
        breaker.record_failure()
        self.assertFalse(breaker.is_open())
