"""Format validation for user-supplied registration fields."""

from __future__ import annotations

import re

from social_platform.common.exceptions import (
    InvalidBioError,
    InvalidEmailError,
    InvalidUsernameError,
)

_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAXIMUM_BIO_LENGTH = 280


def validate_username(username: str) -> None:
    """Raise `InvalidUsernameError` unless `username` is 3-30 letters, digits, or underscores."""
    if not _USERNAME_PATTERN.fullmatch(username):
        raise InvalidUsernameError(
            "Username must be 3-30 characters long and contain only letters, "
            "digits, and underscores."
        )


def validate_email(email: str) -> None:
    """Raise `InvalidEmailError` unless `email` looks like a well-formed email address."""
    if not _EMAIL_PATTERN.fullmatch(email):
        raise InvalidEmailError(f"{email!r} is not a valid email address.")


def validate_bio(bio: str) -> None:
    """Raise `InvalidBioError` if `bio` exceeds the maximum length. An empty bio is fine."""
    if len(bio) > _MAXIMUM_BIO_LENGTH:
        raise InvalidBioError(f"Bio must be at most {_MAXIMUM_BIO_LENGTH} characters long.")
