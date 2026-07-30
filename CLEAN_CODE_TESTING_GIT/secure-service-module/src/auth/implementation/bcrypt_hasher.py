"""BcryptPasswordHasher -- bcrypt-based PasswordHasher."""

import bcrypt

from src.auth.exceptions import InvalidPasswordError
from src.auth.interfaces import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """PasswordHasher implementation using bcrypt's salted hashing."""

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt."""
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> None:
        """Raise InvalidPasswordError if password does not match hashed."""
        if not bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8")):
            raise InvalidPasswordError("Invalid password.")
