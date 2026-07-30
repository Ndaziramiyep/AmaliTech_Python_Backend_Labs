"""Domain-specific exceptions for the grade analytics tool."""

from __future__ import annotations


class StudentDataError(Exception):
    """Base error for all student data processing failures."""


class StudentDataFileNotFoundError(StudentDataError):
    """Raised when a required student data file cannot be located."""


class StudentDataFilePermissionError(StudentDataError):
    """Raised when a student data file cannot be read or written due to permissions."""


class InvalidGradeRecordError(StudentDataError):
    """Raised when a CSV row cannot be parsed into a valid grade record."""
