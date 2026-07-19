"""Unit tests for importer.service.ImportService.

These tests mock the CSV reader and the repository so that the
service's orchestration logic (looping, dispatching to the validator,
building the summary) is exercised in isolation from real file I/O.
End-to-end behaviour against real files is covered in
``tests/test_integration.py``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import DuplicateUserError, FileFormatError
from importer.models import User
from importer.service import ImportService


def _make_reader_mock(mocker: MockerFixture, rows: list[tuple[int, dict[str, str]]]) -> MagicMock:
    reader_instance = MagicMock()
    reader_instance.rows.return_value = iter(rows)
    reader_instance.__enter__.return_value = reader_instance
    reader_instance.__exit__.return_value = False

    reader_class = mocker.patch("importer.service.CsvUserReader")
    reader_class.return_value = reader_instance
    return reader_instance


def _make_repository_factory(mocker: MockerFixture) -> tuple[MagicMock, MagicMock]:
    repo_instance = MagicMock()
    repo_instance.__enter__.return_value = repo_instance
    repo_instance.__exit__.return_value = False

    factory = MagicMock(return_value=repo_instance)
    return factory, repo_instance


def test_import_csv_counts_successful_rows(mocker: MockerFixture) -> None:
    rows = [
        (1, {"user_id": "1", "name": "Alice", "email": "alice@example.com"}),
        (2, {"user_id": "2", "name": "Bob", "email": "bob@example.com"}),
    ]
    _make_reader_mock(mocker, rows)
    factory, repo = _make_repository_factory(mocker)

    service = ImportService()
    summary = service.import_csv("ignored.csv", "ignored.json", repository_factory=factory)

    assert summary.imported == 2
    assert summary.duplicates == []
    assert summary.errors == []
    assert repo.add.call_count == 2


def test_import_csv_records_validation_errors_and_continues(mocker: MockerFixture) -> None:
    rows = [
        (1, {"user_id": "1", "name": "Alice", "email": "alice@example.com"}),
        (2, {"user_id": "2", "name": "", "email": "bob@example.com"}),
        (3, {"user_id": "3", "name": "Carol", "email": "carol@example.com"}),
    ]
    _make_reader_mock(mocker, rows)
    factory, repo = _make_repository_factory(mocker)

    service = ImportService()
    summary = service.import_csv("ignored.csv", "ignored.json", repository_factory=factory)

    assert summary.imported == 2
    assert summary.has_errors
    assert len(summary.errors) == 1
    assert "Row 2" in summary.errors[0]


def test_import_csv_records_duplicates_and_continues(mocker: MockerFixture) -> None:
    rows = [
        (1, {"user_id": "1", "name": "Alice", "email": "alice@example.com"}),
        (2, {"user_id": "1", "name": "Alice Again", "email": "alice2@example.com"}),
    ]
    _make_reader_mock(mocker, rows)
    factory, repo = _make_repository_factory(mocker)
    repo.add.side_effect = [None, DuplicateUserError("1")]

    service = ImportService()
    summary = service.import_csv("ignored.csv", "ignored.json", repository_factory=factory)

    assert summary.imported == 1
    assert summary.duplicates == ["1"]


def test_import_csv_propagates_file_format_error(mocker: MockerFixture) -> None:
    reader_class = mocker.patch("importer.service.CsvUserReader")
    reader_class.return_value.__enter__.side_effect = FileFormatError("bad file")
    factory, _repo = _make_repository_factory(mocker)

    service = ImportService()
    with pytest.raises(FileFormatError):
        service.import_csv("ignored.csv", "ignored.json", repository_factory=factory)


def test_import_csv_uses_injected_validator(mocker: MockerFixture) -> None:
    rows = [(1, {"user_id": "1", "name": "Alice", "email": "alice@example.com"})]
    _make_reader_mock(mocker, rows)
    factory, repo = _make_repository_factory(mocker)

    validator = MagicMock()
    validator.validate.return_value = User(user_id="1", name="Alice", email="alice@example.com")

    service = ImportService(validator=validator)
    summary = service.import_csv("ignored.csv", "ignored.json", repository_factory=factory)

    validator.validate.assert_called_once_with(1, rows[0][1])
    assert summary.imported == 1


def test_import_csv_logs_summary_even_on_empty_file(mocker: MockerFixture) -> None:
    _make_reader_mock(mocker, [])
    factory, _repo = _make_repository_factory(mocker)

    service = ImportService()
    summary = service.import_csv("ignored.csv", "ignored.json", repository_factory=factory)

    assert summary.imported == 0
    assert not summary.has_errors
