import logging

from src.auth.exceptions import (InvalidPasswordError, UserAlreadyExistsError,
                                 UserNotFoundError)
from src.auth.interfaces import PasswordHasher, UserRepository
from src.auth.models import User

logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordHasher
    ):
        self._repo = user_repository
        self._hasher = password_hasher
        self._min_password_length = 8

    def register_user(self, username: str, email: str, password: str) -> User:
        existing_user = self._repo.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError(f"User with email '{email}' already exists.")

        if len(password) < self._min_password_length:
            raise InvalidPasswordError(
                f"Password must be at least {self._min_password_length} characters."
            )

        password_hash = self._hasher.hash_password(password)

        user = User(username=username, email=email, password_hash=password_hash)

        self._repo.add(user)
        logger.info("User registered", extra={"email": user.email})

        return user

    def verify_user(self, email: str, password: str) -> bool:
        """Verify user credentials for login."""
        user = self._repo.get_by_email(email)
        if not user:
            logger.info("User login failed: email not found", extra={"email": email})
            raise UserNotFoundError(f"No user found with email '{email}'.")

        if not self._hasher.verify_password(password, user.password_hash):
            logger.info("User login failed: invalid password", extra={"email": email})
            raise InvalidPasswordError("Invalid password.")

        logger.info("User login success", extra={"email": email})
        return True
