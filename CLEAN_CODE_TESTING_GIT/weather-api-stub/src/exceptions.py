class CityNotFoundError(Exception):
    """Raised when a requested city is not in the predefined list."""

    pass


class InvalidAPIKeyError(Exception):
    """Raised when the API key provided is invalid."""

    pass
