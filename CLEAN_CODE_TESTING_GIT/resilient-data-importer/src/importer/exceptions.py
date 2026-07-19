"""Custom exception hierarchy for the resilient data importer.

All exceptions raised by this package inherit from :class:`ImporterError`,
so callers can catch that single type to handle any importer-specific
failure, or catch a more specific subclass to react to a particular
error case (missing/malformed file, invalid row, duplicate user, or a
storage failure).
"""

from __future__ import annotations


class ImporterError(Exception):
    """Base class for all errors raised by the importer package."""


class FileFormatError(ImporterError):
    """Raised when the source CSV file cannot be read or is malformed.

    Covers cases such as a missing file, an unreadable file, an empty
    file, or a file that is missing one or more required columns.
    """


class RowValidationError(ImporterError):
    """Raised when a single CSV row fails data validation.

    Attributes:
        row_number: The 1-based data row number (header row excluded)
            on which validation failed.
        reason: A human-readable explanation of the validation failure.
    """

    def __init__(self, row_number: int, reason: str) -> None:
        """Initialize the error.

        Args:
            row_number: The 1-based data row number that failed validation.
            reason: A human-readable explanation of the validation failure.
        """
        self.row_number = row_number
        self.reason = reason
        super().__init__(f"Row {row_number}: {reason}")


class DuplicateUserError(ImporterError):
    """Raised when a user_id already exists in the repository.

    Attributes:
        user_id: The identifier that was already present in storage.
    """

    def __init__(self, user_id: str) -> None:
        """Initialize the error.

        Args:
            user_id: The identifier that was already present in storage.
        """
        self.user_id = user_id
        super().__init__(f"Duplicate user_id: {user_id!r}")


class RepositoryError(ImporterError):
    """Raised when the JSON-backed storage layer cannot be read or written."""
