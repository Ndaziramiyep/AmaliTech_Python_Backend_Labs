"""Application-specific exceptions, re-exported for
`from social.exceptions import X`.
"""
from social.exceptions.errors import (
    AlreadyFollowingError,
    AlreadyLikedError,
    DuplicateEmailError,
    DuplicateUsernameError,
    PostNotFoundError,
    SelfFollowError,
    SocialError,
    UnitOfWorkStateError,
    UserNotFoundError,
)

__all__ = [
    "AlreadyFollowingError",
    "AlreadyLikedError",
    "DuplicateEmailError",
    "DuplicateUsernameError",
    "PostNotFoundError",
    "SelfFollowError",
    "SocialError",
    "UnitOfWorkStateError",
    "UserNotFoundError",
]
