import logging

logger = logging.getLogger(__name__)


class ImporterError(Exception):
    """Base class for all importer exceptions."""
    pass


class FileFormatError(ImporterError):
    """Raised when the input file format is invalid."""
    pass


class ValidationError(ImporterError):
    """Raised when user data validation fails."""
    pass


class DuplicateUserError(ImporterError):
    """Raised when a user already exists in the database."""
    pass


class DatabaseError(ImporterError):
    """Raised when a database operation fails."""
    pass
