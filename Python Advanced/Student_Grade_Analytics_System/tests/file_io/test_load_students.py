"""Tests for CSV loading, streaming, and error handling."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from grade_analytics.file_io.load_students import (
    load_grade_records_from_csv,
    load_students_from_csv,
    parse_score,
    stream_grade_records_from_csv,
)
from grade_analytics.models.exceptions import (
    InvalidGradeRecordError,
    StudentDataFileNotFoundError,
    StudentDataFilePermissionError,
)


@pytest.mark.parametrize(
    ("raw_score", "expected"),
    [("88.5", 88.5), (88.5, 88.5), (88, 88.0)],
)
def test_parse_score_accepts_str_int_and_float(
    raw_score: str | float | int, expected: float
) -> None:
    """parse_score handles the Union of str, int, and float inputs a CSV may yield."""
    assert parse_score(raw_score) == expected


def test_parse_score_rejects_non_numeric_value() -> None:
    """A non-numeric score string is reported as an invalid grade record."""
    with pytest.raises(InvalidGradeRecordError):
        parse_score("not-a-number")


def test_parse_score_rejects_out_of_range_value() -> None:
    """A score outside 0-100 is reported as an invalid grade record."""
    with pytest.raises(InvalidGradeRecordError):
        parse_score(150.0)


def test_load_grade_records_from_csv_parses_every_row(sample_csv_file: Path) -> None:
    """Every data row in the CSV becomes one GradeRecord."""
    records = load_grade_records_from_csv(sample_csv_file)
    assert len(records) == 5
    assert records[0].student_id == "S001"
    assert records[0].score == 88.5


def test_stream_grade_records_from_csv_yields_same_records_as_list_loader(
    sample_csv_file: Path,
) -> None:
    """The generator-based loader yields the same records as the list-based one."""
    streamed = list(stream_grade_records_from_csv(sample_csv_file))
    loaded = load_grade_records_from_csv(sample_csv_file)
    assert streamed == loaded


def test_load_students_from_csv_deduplicates_repeated_student_rows(
    sample_csv_file: Path,
) -> None:
    """A student appearing on multiple rows is only returned once."""
    students = load_students_from_csv(sample_csv_file)
    assert [student.student_id for student in students] == ["S001", "S002", "S003"]


def test_load_grade_records_from_csv_raises_for_missing_file(tmp_path: Path) -> None:
    """A missing CSV path raises the domain-specific not-found error."""
    with pytest.raises(StudentDataFileNotFoundError):
        load_grade_records_from_csv(tmp_path / "does_not_exist.csv")


def test_load_grade_records_from_csv_raises_for_permission_error(
    sample_csv_file: Path, mocker: MockerFixture
) -> None:
    """A PermissionError while opening the file is translated to a domain error."""
    mocker.patch("builtins.open", side_effect=PermissionError)
    with pytest.raises(StudentDataFilePermissionError):
        load_grade_records_from_csv(sample_csv_file)


def test_load_grade_records_from_csv_raises_for_missing_column(tmp_path: Path) -> None:
    """A CSV missing a required column raises an invalid-record error."""
    csv_path = tmp_path / "broken.csv"
    csv_path.write_text("student_id,name,major,year\nS001,Alice,CS,2\n", encoding="utf-8")
    with pytest.raises(InvalidGradeRecordError):
        load_grade_records_from_csv(csv_path)


def test_load_students_from_csv_raises_for_invalid_year(tmp_path: Path) -> None:
    """A non-numeric year field raises an invalid-record error."""
    csv_path = tmp_path / "broken.csv"
    csv_path.write_text(
        "student_id,name,major,year,course_code,semester,score\n"
        "S001,Alice,CS,not-a-number,CS201,Fall2023,88.5\n",
        encoding="utf-8",
    )
    with pytest.raises(InvalidGradeRecordError):
        load_students_from_csv(csv_path)
