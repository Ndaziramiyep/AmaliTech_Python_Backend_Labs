"""Custom exceptions for the auth module."""


class UserAlreadyExistsError(Exception):
    """Raised when registering a user with an email that is already taken.

    Example:
        >>> raise UserAlreadyExistsError(
        ...     "User with email 'patrick@gmail.com' already exists."
        ... )
    """


class UserNotFoundError(Exception):
    """Raised when a user with a given email is not found during login.

    Example:
        >>> raise UserNotFoundError("No user found with email 'patrick@gmail.com'.")
    """


class InvalidPasswordError(Exception):
    """Raised when a password fails the registration policy or verification.

    Example:
        >>> raise InvalidPasswordError("Password must be at least 8 characters.")
    """
