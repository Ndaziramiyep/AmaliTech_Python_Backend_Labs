"""Scrypt-based password hashing, shared by registration and authentication."""

from __future__ import annotations

import hashlib
import hmac
import os

_SCRYPT_SALT_LENGTH_BYTES = 16
_SCRYPT_COST_FACTOR = 2**14
_SCRYPT_BLOCK_SIZE = 8
_SCRYPT_PARALLELIZATION = 1


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


def _derive_key(plaintext_password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        plaintext_password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_COST_FACTOR,
        r=_SCRYPT_BLOCK_SIZE,
        p=_SCRYPT_PARALLELIZATION,
    )
