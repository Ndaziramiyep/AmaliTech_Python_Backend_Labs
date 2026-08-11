"""Tests for the structured data models."""

from __future__ import annotations

import dataclasses

import pytest

from grade_analytics.models.entities import Course, GradeRecord, RankedStudent, Student


def test_student_is_immutable() -> None:
    """Student instances are frozen and cannot be mutated after creation."""
    student = Student(student_id="S001", name="Alice Johnson", module="Computer Science", year=2)
    with pytest.raises(dataclasses.FrozenInstanceError):
        student.name = "Someone Else"  # type: ignore[misc]


def test_student_has_no_instance_dict_due_to_slots() -> None:
    """Student uses __slots__, so it has no per-instance __dict__."""
    student = Student(student_id="S001", name="Alice Johnson", module="Computer Science", year=2)
    assert not hasattr(student, "__dict__")


def test_course_defaults_credits_to_three() -> None:
    """Course.credits defaults to 3 when not supplied."""
    course = Course(code="CS201", name="Data Structures")
    assert course.credits == 3


def test_grade_record_fields_are_accessible_by_name() -> None:
    """GradeRecord is a namedtuple exposing named field access."""
    record = GradeRecord(student_id="S001", course_code="CS201", semester="Fall2023", score=88.5)
    assert record.student_id == "S001"
    assert record.score == 88.5


def test_ranked_student_wraps_student_and_average() -> None:
    """RankedStudent bundles a rank, a Student, and their average score."""
    student = Student(student_id="S001", name="Alice Johnson", module="Computer Science", year=2)
    ranked = RankedStudent(rank=1, student=student, average_score=91.0)
    assert ranked.rank == 1
    assert ranked.student is student
    assert ranked.average_score == 91.0
