"""Domain exception hierarchy. No psycopg2/redis/pymongo exception type crosses this boundary."""

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


class CommentNotFoundError(SocialPlatformError):
    """Raised when an operation references a comment that does not exist."""


class InvalidFollowOperationError(SocialPlatformError):
    """Raised when a user attempts to follow or unfollow themselves."""


class InvalidCommentOperationError(SocialPlatformError):
    """Raised when a reply's parent comment belongs to a different post."""


class InvalidBioError(SocialPlatformError):
    """Raised when a bio does not meet the platform's format requirements."""


class OwnershipError(SocialPlatformError):
    """Raised when a user attempts to modify a post or comment they do not own."""


class ConnectionPoolExhaustedError(SocialPlatformError):
    """Raised when no connection is available from the PostgreSQL connection pool."""
