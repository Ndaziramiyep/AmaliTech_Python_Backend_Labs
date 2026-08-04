"""Format validation for user-supplied registration fields."""

from __future__ import annotations

import re

from social_platform.models.exceptions import InvalidEmailError, InvalidUsernameError

_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
