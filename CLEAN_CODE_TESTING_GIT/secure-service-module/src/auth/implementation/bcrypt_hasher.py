"""BcryptPasswordHasher — bcrypt-based implementation of PasswordHasher."""

import bcrypt

from src.auth.interfaces import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """PasswordHasher implementation using the bcrypt algorithm.

    Uses bcrypt's built-in salting to produce a unique hash on every call,
    making rainbow-table and brute-force attacks significantly harder.

    Example:
        >>> hasher = BcryptPasswordHasher()
        >>> hashed = hasher.hash_password("Patrick")
        >>> hasher.verify_password("Patrick", hashed)
        True
    """

    def hash_password(self, password: str) -> str:
        """Hash a plain-text password using bcrypt.

        Args:
            password: The plain-text password to hash.

        Returns:
            A bcrypt-hashed string of the password.
        """
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a plain-text password against a bcrypt hash.

        Args:
            password: The plain-text password to check.
            hashed: The bcrypt hash to compare against.

        Returns:
            True if the password matches the hash, False otherwise.
        """
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed.encode("utf-8"),
        )
