"""Unit tests for the password strength policy."""

from __future__ import annotations

import pytest

from social_platform.common.exceptions import WeakPasswordError
from social_platform.common.security import validate_password_strength


def test_validate_password_strength_accepts_a_strong_password() -> None:
    """A password with lower, upper, digit, special character, and enough length passes."""
    validate_password_strength("Str0ng!Pass")


@pytest.mark.parametrize(
    "weak_password",
    [
        "alllowercase1!",
        "ALLUPPERCASE1!",
        "NoDigitsHere!",
        "NoSpecialChars1",
        "Ab1!",
    ],
)
def test_validate_password_strength_rejects_passwords_missing_a_requirement(
    weak_password: str,
) -> None:
    """Any password missing one of the five requirements is rejected."""
    with pytest.raises(WeakPasswordError):
        validate_password_strength(weak_password)


def test_validate_password_strength_lists_every_unmet_requirement() -> None:
    """The error message enumerates all missing requirements, not just the first."""
    with pytest.raises(WeakPasswordError, match="uppercase.*digit.*special character"):
        validate_password_strength("weak")
