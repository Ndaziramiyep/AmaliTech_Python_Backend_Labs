"""Password security: scrypt-based hashing and the strength policy new passwords must meet."""

from __future__ import annotations

import hashlib
import hmac
import os
import re

from social_platform.common.exceptions import WeakPasswordError

_SCRYPT_SALT_LENGTH_BYTES = 16
_SCRYPT_COST_FACTOR = 2**14
_SCRYPT_BLOCK_SIZE = 8
_SCRYPT_PARALLELIZATION = 1

_MINIMUM_PASSWORD_LENGTH = 8
_LOWERCASE_PATTERN = re.compile(r"[a-z]")
_UPPERCASE_PATTERN = re.compile(r"[A-Z]")
_DIGIT_PATTERN = re.compile(r"\d")
_SPECIAL_CHARACTER_PATTERN = re.compile(r"[^\w\s]")


def hash_password(plaintext_password: str) -> str:
    """Salt and hash a plaintext password as ``salt_hex:derived_key_hex``."""
    salt = os.urandom(_SCRYPT_SALT_LENGTH_BYTES)
    derived_key = _derive_key(plaintext_password, salt)
    return f"{salt.hex()}:{derived_key.hex()}"


def verify_password(plaintext_password: str, password_hash: str) -> bool:
    """Return whether `plaintext_password` matches a hash produced by `hash_password`."""
    salt_hex, _, derived_key_hex = password_hash.partition(":")
    derived_key = _derive_key(plaintext_password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(derived_key, bytes.fromhex(derived_key_hex))


def validate_password_strength(plaintext_password: str) -> None:
    """Raise `WeakPasswordError` unless the password meets every strength requirement."""
    unmet_requirements = [
        requirement
        for requirement, is_satisfied in (
            (
                f"at least {_MINIMUM_PASSWORD_LENGTH} characters",
                len(plaintext_password) >= _MINIMUM_PASSWORD_LENGTH,
            ),
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


def _derive_key(plaintext_password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        plaintext_password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_COST_FACTOR,
        r=_SCRYPT_BLOCK_SIZE,
        p=_SCRYPT_PARALLELIZATION,
    )
