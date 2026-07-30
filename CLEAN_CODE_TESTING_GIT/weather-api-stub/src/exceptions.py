class CityNotFoundError(Exception):
    """Raised when a requested city is not in the predefined data set."""


class InvalidAPIKeyError(Exception):
    """Raised when the API key provided is not recognised."""
