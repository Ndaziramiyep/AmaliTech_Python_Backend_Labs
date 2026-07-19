"""Unit tests for importer.exceptions."""

from __future__ import annotations

import pytest

from importer.exceptions import (
    DuplicateUserError,
    FileFormatError,
    ImporterError,
    RepositoryError,
    RowValidationError,
)


@pytest.mark.parametrize(
    "exc_class",
    [FileFormatError, RepositoryError],
)
def test_simple_errors_are_importer_errors(exc_class: type[ImporterError]) -> None:
    assert issubclass(exc_class, ImporterError)


def test_row_validation_error_carries_context() -> None:
    error = RowValidationError(3, "name is required")
    assert error.row_number == 3
    assert error.reason == "name is required"
    assert "Row 3" in str(error)
    assert "name is required" in str(error)


def test_duplicate_user_error_carries_user_id() -> None:
    error = DuplicateUserError("42")
    assert error.user_id == "42"
    assert "42" in str(error)
