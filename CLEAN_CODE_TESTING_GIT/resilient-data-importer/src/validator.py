import re
import logging
from .models.user import User
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


class UserValidator:
    """Validates user data."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Checks if the email format is valid."""
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(email_regex, email))

    def validate(self, user: User) -> None:
        """Validates all fields of a User object."""
        if not user.user_id or user.user_id <= 0:
            logger.error(f"Invalid user_id: {user.user_id}")
            raise ValidationError(f"Invalid user_id: {user.user_id}")

        if not user.name:
            logger.error("User name is missing")
            raise ValidationError("User name is missing")

        if not self.validate_email(user.email):
            logger.error(f"Invalid email format: {user.email}")
            raise ValidationError(f"Invalid email format: {user.email}")

        logger.debug(f"User {user.user_id} validated successfully")
