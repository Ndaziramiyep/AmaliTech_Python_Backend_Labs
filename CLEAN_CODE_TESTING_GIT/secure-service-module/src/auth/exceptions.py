class UserAlreadyExistsError(Exception):
    """Raised when attempting to register a user with an email that already exists."""

    pass


class UserNotFoundError(Exception):
    """Raised when a user with a given email is not found during login."""

    pass


class InvalidPasswordError(Exception):
    """Raised when a password does not meet policy or verification fails."""

    pass
