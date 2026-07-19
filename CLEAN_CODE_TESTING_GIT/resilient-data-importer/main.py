import argparse
import logging

from src.exceptions import (DatabaseError, DuplicateUserError, FileFormatError,
                            ValidationError)
from src.logging_config import setup_logging
from src.parser import CSVParser
from src.storage import UserRepository
from src.validator import UserValidator

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(description="Resilient Data Importer CLI")
    parser.add_argument("csv_file")
    parser.add_argument("--db", default="data/users.json")
    args = parser.parse_args()

    csv_parser = CSVParser(args.csv_file)
    validator = UserValidator()
    repository = UserRepository(args.db)

    try:
        users = csv_parser.parse()

        if not users:
            logger.warning("No users found in CSV file")
            return

        for user in users:
            try:
                validator.validate(user)
                repository.add_user(user)
                logger.info("User added successfully")
            except ValidationError as ve:
                logger.warning("Validation error: %s", ve)
            except DuplicateUserError:
                logger.warning("Duplicate user skipped")

    except FileNotFoundError as fe:
        logger.error(fe)
    except FileFormatError as ffe:
        logger.error(ffe)
    except DatabaseError as db_err:
        logger.error(db_err)
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)


if __name__ == "__main__":
    main()
