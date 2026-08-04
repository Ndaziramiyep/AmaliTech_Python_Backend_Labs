"""Domain exception hierarchy. No psycopg2/redis/pymongo exception types cross this boundary."""

from __future__ import annotations


class SocialPlatformError(Exception):
    """Root of the domain exception hierarchy."""


class UserNotFoundError(SocialPlatformError):
    """Raised when an operation references a user that does not exist."""


class UserAlreadyExistsError(SocialPlatformError):
    """Raised when registering a user whose username or email is already taken."""


class InvalidCredentialsError(SocialPlatformError):
    """Raised when a login attempt's username or password does not match."""


class InvalidUsernameError(SocialPlatformError):
    """Raised when a username does not meet the platform's format requirements."""


class InvalidEmailError(SocialPlatformError):
    """Raised when an email address is not well-formed."""


class WeakPasswordError(SocialPlatformError):
    """Raised when a password does not meet the platform's strength requirements."""


class PostNotFoundError(SocialPlatformError):
    """Raised when an operation references a post that does not exist."""


class InvalidFollowOperationError(SocialPlatformError):
    """Raised when a user attempts to follow or unfollow themselves."""


class ConnectionPoolExhaustedError(SocialPlatformError):
    """Raised when no connection is available from the PostgreSQL connection pool."""
