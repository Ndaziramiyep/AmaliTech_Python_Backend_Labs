"""Custom exceptions for the auth module."""


class UserAlreadyExistsError(Exception):
    """Raised when a user with the given email already exists."""


class UserNotFoundError(Exception):
    """Raised when no user matches the given email."""


class WeakPasswordError(Exception):
    """Raised at registration when a password fails the strength policy."""


class InvalidPasswordError(Exception):
    """Raised at login when a password does not match the stored hash."""
