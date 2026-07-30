"""Structured data models for students, courses, and grade records.

``Student`` and ``Course`` use slotted, frozen dataclasses so instances are
immutable and avoid a per-instance ``__dict__`` (lower memory footprint when
thousands of records are loaded). ``GradeRecord`` uses a ``NamedTuple``,
which is the lightest structure available for a simple, fixed tuple of
scalar fields read straight off a CSV row.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

Numeric = int | float


@dataclass(frozen=True, slots=True)
class Student:
    """An enrolled student."""

    student_id: str
    name: str
    major: str
    year: int


@dataclass(frozen=True, slots=True)
class Course:
    """A course a student can be graded in."""

    code: str
    name: str
    credits: int = 3


class GradeRecord(NamedTuple):
    """One student's score in one course during one semester."""

    student_id: str
    course_code: str
    semester: str
    score: float


class RankedStudent(NamedTuple):
    """A student's position in a leaderboard, computed from their average score."""

    rank: int
    student: Student
    average_score: float
