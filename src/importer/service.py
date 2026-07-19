"""Import orchestration service.

Ties together CSV parsing (:mod:`importer.parser`), row validation
(:mod:`importer.validator`), and JSON storage (:mod:`importer.repository`)
into a single, resilient import operation, reporting a structured
:class:`ImportSummary` and emitting log records for successes,
warnings (skipped rows), and errors.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from importer.exceptions import DuplicateUserError, FileFormatError, RowValidationError
from importer.parser import CsvUserReader
from importer.repository import JsonUserRepository, UserRepository
from importer.validator import UserRowValidator

logger = logging.getLogger(__name__)


@dataclass
class ImportSummary:
    """Outcome of a single import run.

    Attributes:
        imported: Number of users successfully imported.
        duplicates: user_id values skipped because they already existed.
        errors: Human-readable descriptions of rows that failed validation.
    """

    imported: int = 0
    duplicates: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Return whether any row failed validation during the run."""
        return bool(self.errors)


class ImportService:
    """Coordinates reading, validating, and persisting user records."""

    def __init__(self, validator: UserRowValidator | None = None) -> None:
        """Initialize the service.

        Args:
            validator: Row validator to use. Defaults to a new
                :class:`UserRowValidator` instance, but a mock can be
                injected here for testing (dependency inversion).
        """
        self._validator = validator or UserRowValidator()

    def import_csv(
        self,
        csv_path: Path | str,
        db_path: Path | str,
        repository_factory: type[UserRepository] = JsonUserRepository,
    ) -> ImportSummary:
        """Import users from ``csv_path`` into the repository at ``db_path``.

        Args:
            csv_path: Path to the source CSV file.
            db_path: Path to the JSON database file.
            repository_factory: Callable used to construct the repository,
                overridable for testing with a mock/in-memory repository.

        Returns:
            An :class:`ImportSummary` describing what happened.

        Raises:
            FileFormatError: If the CSV file is missing, empty, or missing
                required columns.
            RepositoryError: If the database file exists but cannot be
                read, or cannot be written back to disk.
        """
        summary = ImportSummary()
        try:
            with repository_factory(db_path) as repository, CsvUserReader(csv_path) as reader:
                for row_number, raw_row in reader.rows():
                    try:
                        user = self._validator.validate(row_number, raw_row)
                        repository.add(user)
                    except RowValidationError as exc:
                        logger.warning("Skipping invalid row: %s", exc)
                        summary.errors.append(str(exc))
                    except DuplicateUserError as exc:
                        logger.warning("Skipping duplicate: %s", exc)
                        summary.duplicates.append(exc.user_id)
                    else:
                        summary.imported += 1
                        logger.info("Imported user %s", user.user_id)
        except FileFormatError as exc:
            logger.error("Import aborted, bad CSV file: %s", exc)
            raise
        finally:
            logger.info(
                "Import finished: %d imported, %d duplicate(s), %d error(s)",
                summary.imported,
                len(summary.duplicates),
                len(summary.errors),
            )
        return summary
