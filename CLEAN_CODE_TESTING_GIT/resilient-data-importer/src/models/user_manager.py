import csv
import logging
from .user import User

logger = logging.getLogger(__name__)


class UserManager:
    """Manages users stored in CSV files."""

    def __init__(self, file_path):
        self.file_path = file_path
        self.users: list[User] = []

    def add_user(self, user: User):
        """Add user to memory."""
        self.users.append(user)

    def find_user(self, email: str) -> User | None:
        """Retrieve user by email."""
        for user in self.users:
            if user.email == email:
                return user
        return None

    def load_users(self):
        """Load users from CSV."""
        try:
            with open(self.file_path, newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                try:
                    next(reader)  # skip header
                except StopIteration:
                    return

                for row in reader:
                    if len(row) >= 3:
                        user = User(user_id=int(row[0]), name=row[1], email=row[2])
                        self.users.append(user)
        except FileNotFoundError:
            logger.warning("File not found: %s", self.file_path)
            self.users = []
        except Exception as e:
            logger.error("Error loading users: %s", e)

    def save_users(self):
        """Save users to CSV."""
        try:
            with open(self.file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["user_id", "name", "email"])
                for user in self.users:
                    writer.writerow([user.user_id, user.name, user.email])
        except Exception as e:
            logger.error("Error saving users: %s", e)
