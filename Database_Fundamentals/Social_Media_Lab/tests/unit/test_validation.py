"""Unit tests for username/email format validation."""

from __future__ import annotations

import pytest

from social_platform.common.exceptions import InvalidEmailError, InvalidUsernameError
from social_platform.common.validation import validate_email, validate_username


@pytest.mark.parametrize("valid_username", ["ada", "grace_hopper", "user123", "a" * 30])
def test_validate_username_accepts_valid_usernames(valid_username: str) -> None:
    """Letters, digits, and underscores, 3-30 characters long, are all accepted."""
    validate_username(valid_username)


@pytest.mark.parametrize(
    "invalid_username",
    ["ab", "a" * 31, "has space", "has-hyphen", "has@symbol", ""],
)
def test_validate_username_rejects_invalid_usernames(invalid_username: str) -> None:
    """Too short, too long, or containing disallowed characters is rejected."""
    with pytest.raises(InvalidUsernameError):
        validate_username(invalid_username)


@pytest.mark.parametrize("valid_email", ["ada@example.com", "grace.hopper@sub.example.co"])
def test_validate_email_accepts_valid_emails(valid_email: str) -> None:
    """A well-formed local@domain.tld address is accepted."""
    validate_email(valid_email)


@pytest.mark.parametrize(
    "invalid_email", ["not-an-email", "missing-domain@", "@missing-local.com", "no-at-sign.com"]
)
def test_validate_email_rejects_invalid_emails(invalid_email: str) -> None:
    """Anything not shaped like local@domain.tld is rejected."""
    with pytest.raises(InvalidEmailError):
        validate_email(invalid_email)
