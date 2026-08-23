"""Application-specific exception hierarchy.

Beyond `UnitOfWorkStateError`, every exception here is a repository
translating one specific Postgres constraint violation (looked up by
constraint name, not by parsing the driver's error message) into a clear,
catchable, driver-independent type - see the `except psycopg2.errors.*`
blocks in `repositories/*.py`. A caller (a test, a future API layer) can
catch `DuplicateUsernameError` without knowing or caring that it's backed
by a UNIQUE constraint named `users_username_key`.
"""


class SocialError(Exception):
    """Base class for every error raised intentionally by this application."""


class UnitOfWorkStateError(SocialError, RuntimeError):
    """Raised when a UnitOfWork's cursor is read outside its `with` block."""


class DuplicateUsernameError(SocialError):
    """Raised by UserRepository.create when the username is already taken."""


class DuplicateEmailError(SocialError):
    """Raised by UserRepository.create when the email is already registered."""


class UserNotFoundError(SocialError):
    """Raised when an operation references a user id that doesn't exist."""


class PostNotFoundError(SocialError):
    """Raised when an operation references a post id that doesn't exist."""


class SelfFollowError(SocialError):
    """Raised by FollowerRepository.create when follower_id == followee_id."""


class AlreadyFollowingError(SocialError):
    """Raised by FollowerRepository.create when that follow edge already exists."""


class AlreadyLikedError(SocialError):
    """Raised by LikeRepository.create when that user already liked that post."""
