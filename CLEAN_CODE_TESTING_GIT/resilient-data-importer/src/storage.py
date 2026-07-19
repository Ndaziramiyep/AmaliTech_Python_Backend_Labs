import json
import logging
import os
from .models.user import User
from .exceptions import DuplicateUserError, DatabaseError

logger = logging.getLogger(__name__)


class UserRepository:
    """Manages user storage in a JSON file."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.users: dict = {}
        self._load_database()

    def _load_database(self):
        """Loads data from the JSON file."""
        if not os.path.exists(self.db_path):
            self.users = {}
            return

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    self.users = {}
                else:
                    self.users = json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to load database: {e}")
            self.users = {}

    def _save_data(self):
        """Saves current users to the JSON file."""
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            raise DatabaseError(f"Failed to save to database: {e}")

    def user_exists(self, user_id: int) -> bool:
        """Checks if a user with the given ID already exists."""
        return str(user_id) in self.users

    def add_user(self, user: User):
        """Adds a new user to the JSON storage."""
        if self.user_exists(user.user_id):
            logger.warning(f"Attempted to add duplicate user: {user.user_id}")
            raise DuplicateUserError(f"User with ID {user.user_id} already exists")

        self.users[str(user.user_id)] = {
            "name": user.name,
            "email": user.email
        }
        self._save_data()
        logger.info(f"Added user {user.user_id} to database")
