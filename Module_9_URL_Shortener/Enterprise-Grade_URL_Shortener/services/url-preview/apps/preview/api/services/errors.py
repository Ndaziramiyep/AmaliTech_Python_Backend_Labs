class InvalidURLError(Exception):
    """The submitted URL failed validation, or its hostname resolves to a disallowed (private/loopback/reserved) address."""


class CircuitOpenError(Exception):
    """The destination domain's circuit breaker is currently open; the fetch was skipped entirely, with no network call."""


class PreviewFetchError(Exception):
    """The destination page couldn't be fetched or parsed, after all retry attempts were exhausted."""
