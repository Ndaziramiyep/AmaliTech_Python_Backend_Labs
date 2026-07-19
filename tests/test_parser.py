"""Unit tests for importer.parser.CsvUserReader."""

from __future__ import annotations

from pathlib import Path

import pytest

from importer.exceptions import FileFormatError
from importer.parser import CsvUserReader


def test_reads_all_valid_rows(valid_csv_path: Path) -> None:
    with CsvUserReader(valid_csv_path) as reader:
        rows = list(reader.rows())

    assert [r for _, r in rows] == [
        {"user_id": "1", "name": "Alice Uwimana", "email": "alice@example.com"},
        {"user_id": "2", "name": "Bob Habimana", "email": "bob@example.com"},
        {"user_id": "3", "name": "Chantal Mukamana", "email": "chantal@example.com"},
    ]
    assert [n for n, _ in rows] == [1, 2, 3]


def test_missing_file_raises_file_format_error(missing_csv_path: Path) -> None:
    with pytest.raises(FileFormatError, match="not found"), CsvUserReader(missing_csv_path):
        pass


def test_empty_file_raises_file_format_error(empty_csv_path: Path) -> None:
    with pytest.raises(FileFormatError, match="empty"), CsvUserReader(empty_csv_path):
        pass


def test_missing_required_column_raises_file_format_error(
    missing_column_csv_path: Path,
) -> None:
    with (
        pytest.raises(FileFormatError, match="missing required column"),
        CsvUserReader(missing_column_csv_path),
    ):
        pass


def test_rows_outside_context_manager_raises_runtime_error(valid_csv_path: Path) -> None:
    reader = CsvUserReader(valid_csv_path)
    with pytest.raises(RuntimeError):
        list(reader.rows())


def test_file_handle_closed_after_context_exit(valid_csv_path: Path) -> None:
    with CsvUserReader(valid_csv_path) as reader:
        list(reader.rows())
    assert reader._file is None  # noqa: SLF001 - verifying internal cleanup


def test_directory_instead_of_file_raises_file_format_error(tmp_path: Path) -> None:
    with pytest.raises(FileFormatError), CsvUserReader(tmp_path):
        pass
