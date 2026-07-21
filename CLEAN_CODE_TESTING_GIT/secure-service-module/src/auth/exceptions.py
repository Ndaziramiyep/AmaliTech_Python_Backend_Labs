"""Custom exceptions for the auth module."""


class UserAlreadyExistsError(Exception):
    """Raised when attempting to register a user with an email that already exists.

    Example:
        >>> raise UserAlreadyExistsError("User with email 'patrick@example.com' already exists.")
    """


class UserNotFoundError(Exception):
    """Raised when a user with a given email is not found during login.

    Example:
        >>> raise UserNotFoundError("No user found with email 'patrick@example.com'.")
    """


class InvalidPasswordError(Exception):
    """Raised when a password does not meet policy or verification fails.

    Example:
        >>> raise InvalidPasswordError("Password must be at least 7 characters.")
    """
