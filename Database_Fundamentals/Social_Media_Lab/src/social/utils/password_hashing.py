"""PBKDF2-HMAC password hashing (stdlib only) that stores the iteration count alongside the salt and hash so it can be raised later without invalidating already-hashed passwords."""
import hashlib
import hmac
import secrets

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    """Hashes a password with a fresh random salt using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Checks whether a password matches a stored PBKDF2-HMAC hash."""
    try:
        iterations_str, salt_hex, digest_hex = password_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations_str))
    return hmac.compare_digest(actual, expected)
