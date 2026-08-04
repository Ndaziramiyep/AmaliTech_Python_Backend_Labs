"""Unit tests for the shared scrypt password hashing helpers."""

from __future__ import annotations

from social_platform.security.password_hashing import hash_password, verify_password


def test_verify_password_accepts_the_correct_password() -> None:
    """A hash produced by `hash_password` verifies against the same plaintext."""
    password_hash = hash_password("super-secret")

    assert verify_password("super-secret", password_hash) is True


def test_verify_password_rejects_an_incorrect_password() -> None:
    """A hash produced by `hash_password` does not verify against a different plaintext."""
    password_hash = hash_password("super-secret")

    assert verify_password("wrong-password", password_hash) is False


def test_hash_password_salts_identical_passwords_differently() -> None:
    """Each call uses a fresh random salt, so identical passwords hash differently."""
    first_hash = hash_password("super-secret")
    second_hash = hash_password("super-secret")

    assert first_hash != second_hash
    assert verify_password("super-secret", first_hash) is True
    assert verify_password("super-secret", second_hash) is True
