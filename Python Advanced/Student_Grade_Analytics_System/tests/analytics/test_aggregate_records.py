"""Tests for Counter/defaultdict/OrderedDict-based aggregation."""

from __future__ import annotations

from collections import Counter, OrderedDict

from grade_analytics.analytics.aggregate_records import (
    count_grade_distribution,
    group_scores_by_semester,
    group_scores_by_student,
    group_students_by_major,
    group_students_by_year,
    order_grade_distribution,
)
from grade_analytics.models.entities import GradeRecord, Student


def test_count_grade_distribution_tallies_letter_grades(
    sample_grade_records: list[GradeRecord],
) -> None:
    """Each record's score is converted to a letter grade and tallied."""
    distribution = count_grade_distribution(sample_grade_records)
    assert distribution == Counter({"A": 1, "B": 1, "C": 2, "F": 1})


def test_order_grade_distribution_is_in_a_to_f_order() -> None:
    """The ordered distribution lists grades A through F regardless of count order."""
    distribution = Counter({"F": 1, "A": 3, "C": 2})
    ordered = order_grade_distribution(distribution)
    assert isinstance(ordered, OrderedDict)
    assert list(ordered.items()) == [("A", 3), ("C", 2), ("F", 1)]


def test_order_grade_distribution_omits_absent_grades() -> None:
    """Grades with zero occurrences are not present in the ordered result."""
    ordered = order_grade_distribution(Counter({"B": 4}))
    assert list(ordered.keys()) == ["B"]


def test_group_students_by_major_groups_correctly(sample_students: list[Student]) -> None:
    """Students are grouped into lists keyed by their major."""
    grouped = group_students_by_major(sample_students)
    assert {student.student_id for student in grouped["Computer Science"]} == {"S001", "S002"}
    assert {student.student_id for student in grouped["Mathematics"]} == {"S003"}


def test_group_students_by_major_missing_key_returns_empty_list(
    sample_students: list[Student],
) -> None:
    """defaultdict semantics: an absent major key yields an empty list, not a KeyError."""
    grouped = group_students_by_major(sample_students)
    assert grouped["Physics"] == []


def test_group_students_by_year_groups_correctly(sample_students: list[Student]) -> None:
    """Students are grouped into lists keyed by their enrollment year."""
    grouped = group_students_by_year(sample_students)
    assert [student.student_id for student in grouped[2]] == ["S001"]


def test_group_scores_by_student_collects_all_scores(
    sample_grade_records: list[GradeRecord],
) -> None:
    """Every score for a student is collected into that student's list."""
    grouped = group_scores_by_student(sample_grade_records)
    assert grouped["S001"] == [88.5, 93.5]


def test_group_scores_by_semester_collects_all_scores(
    sample_grade_records: list[GradeRecord],
) -> None:
    """Every score in a semester is collected into that semester's list."""
    grouped = group_scores_by_semester(sample_grade_records)
    assert grouped["Fall2023"] == [88.5, 72.0, 55.0]
