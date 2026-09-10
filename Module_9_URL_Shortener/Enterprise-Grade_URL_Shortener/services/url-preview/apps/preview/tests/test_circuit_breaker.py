import fakeredis
from django.test import SimpleTestCase

from apps.preview.api.services.circuit_breaker import DomainCircuitBreaker
from apps.preview.api.services.errors import CircuitOpenError


class DomainCircuitBreakerTests(SimpleTestCase):
    def setUp(self):
        self.redis = fakeredis.FakeStrictRedis(decode_responses=True)
        self.breaker = DomainCircuitBreaker(self.redis, failure_threshold=3, open_seconds=60)

    def test_closed_by_default(self):
        self.breaker.raise_if_open("example.com")  # must not raise

    def test_stays_closed_below_the_failure_threshold(self):
        for _ in range(2):
            self.breaker.record_failure("example.com")

        self.breaker.raise_if_open("example.com")  # must not raise

    def test_opens_after_threshold_consecutive_failures(self):
        for _ in range(3):
            self.breaker.record_failure("example.com")

        with self.assertRaises(CircuitOpenError):
            self.breaker.raise_if_open("example.com")

    def test_success_closes_the_circuit_and_clears_the_failure_count(self):
        for _ in range(3):
            self.breaker.record_failure("example.com")
        self.breaker.record_success("example.com")

        self.breaker.raise_if_open("example.com")  # must not raise

        # The failure counter was cleared too, not just the open flag — one
        # more failure alone shouldn't immediately reopen it.
        self.breaker.record_failure("example.com")
        self.breaker.raise_if_open("example.com")  # must not raise

    def test_failures_on_one_domain_never_affect_another(self):
        for _ in range(3):
            self.breaker.record_failure("a.example.com")

        self.breaker.raise_if_open("b.example.com")  # must not raise
