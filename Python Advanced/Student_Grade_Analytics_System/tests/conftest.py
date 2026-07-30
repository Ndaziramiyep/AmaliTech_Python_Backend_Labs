"""Shared pytest fixtures for the grade analytics test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from grade_analytics.models.entities import GradeRecord, Student

SAMPLE_CSV_HEADER = "student_id,name,major,year,course_code,semester,score\n"

SAMPLE_CSV_ROWS = (
    "S001,Alice Johnson,Computer Science,2,CS201,Fall2023,88.5\n"
    "S001,Alice Johnson,Computer Science,2,CS201,Spring2024,93.5\n"
    "S002,Brian Lee,Computer Science,3,CS305,Fall2023,72.0\n"
    "S002,Brian Lee,Computer Science,3,CS305,Spring2024,79.5\n"
    "S003,Carla Mendes,Mathematics,1,MATH210,Fall2023,55.0\n"
)


@pytest.fixture
def sample_students() -> list[Student]:
    """Three students spread across two majors."""
    return [
        Student(student_id="S001", name="Alice Johnson", major="Computer Science", year=2),
        Student(student_id="S002", name="Brian Lee", major="Computer Science", year=3),
        Student(student_id="S003", name="Carla Mendes", major="Mathematics", year=1),
    ]


@pytest.fixture
def sample_grade_records() -> list[GradeRecord]:
    """Grade records matching :func:`sample_students`."""
    return [
        GradeRecord(student_id="S001", course_code="CS201", semester="Fall2023", score=88.5),
        GradeRecord(student_id="S001", course_code="CS201", semester="Spring2024", score=93.5),
        GradeRecord(student_id="S002", course_code="CS305", semester="Fall2023", score=72.0),
        GradeRecord(student_id="S002", course_code="CS305", semester="Spring2024", score=79.5),
        GradeRecord(student_id="S003", course_code="MATH210", semester="Fall2023", score=55.0),
    ]


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """A temporary CSV file containing :data:`SAMPLE_CSV_ROWS`."""
    csv_path = tmp_path / "students.csv"
    csv_path.write_text(SAMPLE_CSV_HEADER + SAMPLE_CSV_ROWS, encoding="utf-8")
    return csv_path
