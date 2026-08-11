"""Shared pytest fixtures for the grade analytics test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from grade_analytics.models.entities import GradeRecord, Student

SAMPLE_CSV_HEADER = "student_id,name,module,year,course_code,semester,score\n"

SAMPLE_CSV_ROWS = (
    "S001,Alice Johnson,Computer Science,2,CS201,Semester 1,88.5\n"
    "S001,Alice Johnson,Computer Science,2,CS201,Semester 2,93.5\n"
    "S002,Brian Lee,Computer Science,3,CS305,Semester 1,72.0\n"
    "S002,Brian Lee,Computer Science,3,CS305,Semester 2,79.5\n"
    "S003,Carla Mendes,Mathematics,1,MATH210,Semester 1,55.0\n"
)


@pytest.fixture
def sample_students() -> list[Student]:
    """Three students spread across two modules."""
    return [
        Student(student_id="S001", name="Alice Johnson", module="Computer Science", year=2),
        Student(student_id="S002", name="Brian Lee", module="Computer Science", year=3),
        Student(student_id="S003", name="Carla Mendes", module="Mathematics", year=1),
    ]


@pytest.fixture
def sample_grade_records() -> list[GradeRecord]:
    """Grade records matching :func:`sample_students`."""
    return [
        GradeRecord(student_id="S001", course_code="CS201", semester="Semester 1", score=88.5),
        GradeRecord(student_id="S001", course_code="CS201", semester="Semester 2", score=93.5),
        GradeRecord(student_id="S002", course_code="CS305", semester="Semester 1", score=72.0),
        GradeRecord(student_id="S002", course_code="CS305", semester="Semester 2", score=79.5),
        GradeRecord(student_id="S003", course_code="MATH210", semester="Semester 1", score=55.0),
    ]


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """A temporary CSV file containing :data:`SAMPLE_CSV_ROWS`."""
    csv_path = tmp_path / "students.csv"
    csv_path.write_text(SAMPLE_CSV_HEADER + SAMPLE_CSV_ROWS, encoding="utf-8")
    return csv_path
