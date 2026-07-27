"""Tests for BcryptPasswordHasher."""

import pytest

from src.auth.exceptions import InvalidPasswordError
from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher


def test_bcrypt_hasher_produces_a_different_string_than_the_password():
    """Hashing a password never returns the plain-text password itself."""
    hasher = BcryptPasswordHasher()

    hashed = hasher.hash_password("SecurePass1")

    assert hashed != "SecurePass1"


def test_bcrypt_hasher_verifies_the_correct_password():
    """A password verifies successfully against its own bcrypt hash."""
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash_password("SecurePass1")

    assert hasher.verify_password("SecurePass1", hashed) is None


def test_bcrypt_hasher_rejects_the_wrong_password():
    """A different password raises InvalidPasswordError against an existing hash."""
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash_password("SecurePass1")

    with pytest.raises(InvalidPasswordError):
        hasher.verify_password("WrongPassword", hashed)
