"""End-to-end integration tests exercising real files on disk.

Unlike ``tests/test_service.py`` (which mocks the reader/repository to
isolate the service's orchestration logic), these tests run the full
CSV -> validate -> JSON stack against real temporary files, matching
how the CLI actually behaves.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from importer.exceptions import FileFormatError
from importer.service import ImportService


def test_full_import_of_valid_csv(valid_csv_path: Path, db_path: Path) -> None:
    service = ImportService()
    summary = service.import_csv(valid_csv_path, db_path)

    assert summary.imported == 3
    assert summary.duplicates == []
    assert summary.errors == []

    stored = json.loads(db_path.read_text(encoding="utf-8"))
    assert set(stored.keys()) == {"1", "2", "3"}


def test_full_import_with_errors_and_duplicates(mixed_csv_path: Path, db_path: Path) -> None:
    service = ImportService()
    summary = service.import_csv(mixed_csv_path, db_path)

    # Valid rows: user_id 1, 3(invalid email - excluded), 4 -> imported = 2 (1, 4)
    assert summary.imported == 2
    assert summary.duplicates == ["1"]
    assert len(summary.errors) == 2  # blank name (row 2) + invalid email (row 3)

    stored = json.loads(db_path.read_text(encoding="utf-8"))
    assert set(stored.keys()) == {"1", "4"}


def test_import_against_pre_populated_database(
    valid_csv_path: Path, populated_db_path: Path
) -> None:
    service = ImportService()
    summary = service.import_csv(valid_csv_path, populated_db_path)

    # user_id "1" already existed in populated_db_path -> duplicate.
    assert summary.imported == 2
    assert summary.duplicates == ["1"]

    stored = json.loads(populated_db_path.read_text(encoding="utf-8"))
    assert set(stored.keys()) == {"1", "2", "3"}
    assert stored["1"]["name"] == "Existing User"  # original entry preserved


def test_missing_csv_file_raises_and_leaves_database_untouched(
    missing_csv_path: Path, db_path: Path
) -> None:
    service = ImportService()
    with pytest.raises(FileFormatError):
        service.import_csv(missing_csv_path, db_path)

    assert not db_path.exists()
