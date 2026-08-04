"""Strength requirements enforced on new/changed passwords."""

from __future__ import annotations

import re

from social_platform.models.exceptions import WeakPasswordError

_MINIMUM_LENGTH = 8
_LOWERCASE_PATTERN = re.compile(r"[a-z]")
_UPPERCASE_PATTERN = re.compile(r"[A-Z]")
_DIGIT_PATTERN = re.compile(r"\d")
_SPECIAL_CHARACTER_PATTERN = re.compile(r"[^\w\s]")


def validate_password_strength(plaintext_password: str) -> None:
    """Raise `WeakPasswordError` unless the password meets every strength requirement."""
    unmet_requirements = [
        requirement
        for requirement, is_satisfied in (
            (f"at least {_MINIMUM_LENGTH} characters", len(plaintext_password) >= _MINIMUM_LENGTH),
            ("a lowercase letter", _LOWERCASE_PATTERN.search(plaintext_password) is not None),
            ("an uppercase letter", _UPPERCASE_PATTERN.search(plaintext_password) is not None),
            ("a digit", _DIGIT_PATTERN.search(plaintext_password) is not None),
            (
                "a special character",
                _SPECIAL_CHARACTER_PATTERN.search(plaintext_password) is not None,
            ),
        )
        if not is_satisfied
    ]
    if unmet_requirements:
        raise WeakPasswordError("Password must contain " + ", ".join(unmet_requirements) + ".")
