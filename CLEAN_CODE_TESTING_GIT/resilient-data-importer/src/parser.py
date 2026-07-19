import csv
import logging

from .exceptions import FileFormatError
from .models.user import User

logger = logging.getLogger(__name__)


class CSVParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> list[User]:
        users: list[User] = []

        try:
            with open(self.file_path, newline="", encoding="utf-8") as file:
                reader = csv.reader(file)

                try:
                    header = next(reader)
                except StopIteration:
                    logger.warning("CSV file is empty")
                    return []

                if header != ["user_id", "name", "email"]:
                    raise FileFormatError("Invalid CSV headers")

                for row_num, row in enumerate(reader, start=2):
                    try:
                        user = User(
                            user_id=int(row[0]),
                            name=row[1].strip(),
                            email=row[2].strip(),
                        )
                        users.append(user)
                    except (ValueError, IndexError):
                        logger.warning("Skipping malformed row %d: %s", row_num, row)

        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {self.file_path}")

        logger.info("Parsed %d users", len(users))
        return users
