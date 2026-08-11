"""Load student and grade-record data out of CSV files (read access only)."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path
from typing import Union

from grade_analytics.models.entities import GradeRecord, Student
from grade_analytics.models.exceptions import (
    InvalidGradeRecordError,
    StudentDataFileNotFoundError,
    StudentDataFilePermissionError,
)

ScoreInput = Union[str, float, int]  # noqa: UP007 -- explicit Union per assessment requirements

# Default location of the input CSV this module reads.
csv_file_path = Path("data/sample_students.csv")


def parse_score(value: ScoreInput) -> float:
    """Parse a score that may arrive as a ``str``, ``int``, or ``float``."""
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidGradeRecordError(f"Score {value!r} is not numeric") from exc
    if not 0.0 <= score <= 100.0:
        raise InvalidGradeRecordError(f"Score {score} is outside the valid 0-100 range")
    return score


def _row_to_grade_record(row: dict[str, str]) -> GradeRecord:
    try:
        return GradeRecord(
            student_id=row["student_id"],
            course_code=row["course_code"],
            semester=row["semester"],
            score=parse_score(row["score"]),
        )
    except KeyError as exc:
        raise InvalidGradeRecordError(f"CSV row is missing column {exc}") from exc


def _row_to_student(row: dict[str, str]) -> Student:
    try:
        return Student(
            student_id=row["student_id"],
            name=row["name"],
            module=row["module"],
            year=int(row["year"]),
        )
    except (KeyError, ValueError) as exc:
        raise InvalidGradeRecordError(f"CSV row has an invalid student field: {exc}") from exc


def _open_csv_rows(path: Path | str) -> Iterator[dict[str, str]]:
    """Open ``path`` for reading (read access) and yield each row as a ``dict``."""
    csv_path = Path(path)
    try:
        with open(csv_path, newline="", encoding="utf-8") as csv_file:
            yield from csv.DictReader(csv_file)
    except FileNotFoundError as exc:
        raise StudentDataFileNotFoundError(f"CSV file not found: {csv_path}") from exc
    except PermissionError as exc:
        raise StudentDataFilePermissionError(f"Cannot read CSV file: {csv_path}") from exc


def _reject_duplicates(records: Iterator[GradeRecord]) -> Iterator[GradeRecord]:
    """Raise if the same student's same course is recorded twice in one semester."""
    seen: set[tuple[str, str, str]] = set()
    for record in records:
        key = (record.student_id, record.semester, record.course_code)
        if key in seen:
            raise InvalidGradeRecordError(
                f"Student {record.student_id!r} already has a {record.semester!r} score "
                f"for course {record.course_code!r}"
            )
        seen.add(key)
        yield record


def load_grade_records_from_csv(path: Path | str = csv_file_path) -> list[GradeRecord]:
    """Read every grade record from the CSV file at ``path`` into a list."""
    return list(_reject_duplicates(_row_to_grade_record(row) for row in _open_csv_rows(path)))


def stream_grade_records_from_csv(path: Path | str = csv_file_path) -> Iterator[GradeRecord]:
    """Read grade records from the CSV file at ``path`` one row at a time (read access)."""
    yield from _reject_duplicates(_row_to_grade_record(row) for row in _open_csv_rows(path))


def load_students_from_csv(path: Path | str = csv_file_path) -> list[Student]:
    """Read the unique students referenced in the CSV file at ``path``.

    Order of first appearance is preserved.
    """
    students: dict[str, Student] = {}
    for row in _open_csv_rows(path):
        student = _row_to_student(row)
        students.setdefault(student.student_id, student)
    return list(students.values())
