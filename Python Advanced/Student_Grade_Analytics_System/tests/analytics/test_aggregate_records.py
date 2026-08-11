"""Tests for Counter/defaultdict/OrderedDict-based aggregation."""

from __future__ import annotations

from collections import Counter, OrderedDict

from grade_analytics.analytics.aggregate_records import (
    count_grade_distribution,
    group_records_by_year_and_semester,
    group_scores_by_semester,
    group_scores_by_student,
    group_scores_by_student_and_course,
    group_students_by_module,
    group_students_by_year,
    group_students_by_year_and_semester,
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


def test_group_students_by_module_groups_correctly(sample_students: list[Student]) -> None:
    """Students are grouped into lists keyed by their module."""
    grouped = group_students_by_module(sample_students)
    assert {student.student_id for student in grouped["Computer Science"]} == {"S001", "S002"}
    assert {student.student_id for student in grouped["Mathematics"]} == {"S003"}


def test_group_students_by_module_missing_key_returns_empty_list(
    sample_students: list[Student],
) -> None:
    """defaultdict semantics: an absent module key yields an empty list, not a KeyError."""
    grouped = group_students_by_module(sample_students)
    assert grouped["Physics"] == []


def test_group_students_by_year_groups_correctly(sample_students: list[Student]) -> None:
    """Students are grouped into lists keyed by their enrollment year."""
    grouped = group_students_by_year(sample_students)
    assert [student.student_id for student in grouped[2]] == ["S001"]


def test_group_students_by_year_and_semester_groups_correctly(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """Students are grouped into lists keyed by (enrollment year, semester) pairs."""
    grouped = group_students_by_year_and_semester(sample_students, sample_grade_records)
    assert [student.student_id for student in grouped[(2, "Semester 1")]] == ["S001"]
    assert [student.student_id for student in grouped[(2, "Semester 2")]] == ["S001"]
    assert [student.student_id for student in grouped[(3, "Semester 1")]] == ["S002"]
    assert [student.student_id for student in grouped[(1, "Semester 1")]] == ["S003"]


def test_group_students_by_year_and_semester_deduplicates_multiple_records(
    sample_students: list[Student],
) -> None:
    """A student with two records in the same semester appears only once in that group."""
    records = [
        GradeRecord(student_id="S001", course_code="CS201", semester="Semester 1", score=88.5),
        GradeRecord(student_id="S001", course_code="CS305", semester="Semester 1", score=91.0),
    ]
    grouped = group_students_by_year_and_semester(sample_students, records)
    assert [student.student_id for student in grouped[(2, "Semester 1")]] == ["S001"]


def test_group_students_by_year_and_semester_missing_key_returns_empty_list(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """defaultdict semantics: an absent (year, semester) key yields an empty list."""
    grouped = group_students_by_year_and_semester(sample_students, sample_grade_records)
    assert grouped[(4, "Semester 1")] == []


def test_group_records_by_year_and_semester_groups_correctly(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """Records are grouped into lists keyed by (student's enrollment year, semester) pairs."""
    grouped = group_records_by_year_and_semester(sample_students, sample_grade_records)
    assert [record.score for record in grouped[(2, "Semester 1")]] == [88.5]
    assert [record.score for record in grouped[(3, "Semester 2")]] == [79.5]


def test_group_records_by_year_and_semester_missing_key_returns_empty_list(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """defaultdict semantics: an absent (year, semester) key yields an empty list."""
    grouped = group_records_by_year_and_semester(sample_students, sample_grade_records)
    assert grouped[(4, "Semester 1")] == []


def test_group_scores_by_student_collects_all_scores(
    sample_grade_records: list[GradeRecord],
) -> None:
    """Every score for a student is collected into that student's list."""
    grouped = group_scores_by_student(sample_grade_records)
    assert grouped["S001"] == [88.5, 93.5]


def test_group_scores_by_student_and_course_maps_each_course_to_its_score() -> None:
    """Each student's scores are collected into a {course_code: score} mapping."""
    records = [
        GradeRecord(student_id="S001", course_code="CSC", semester="Semester 1", score=88.5),
        GradeRecord(student_id="S001", course_code="Math", semester="Semester 1", score=91.0),
        GradeRecord(student_id="S002", course_code="CSC", semester="Semester 1", score=59.5),
    ]
    grouped = group_scores_by_student_and_course(records)
    assert grouped["S001"] == {"CSC": 88.5, "Math": 91.0}
    assert grouped["S002"] == {"CSC": 59.5}


def test_group_scores_by_semester_collects_all_scores(
    sample_grade_records: list[GradeRecord],
) -> None:
    """Every score in a semester is collected into that semester's list."""
    grouped = group_scores_by_semester(sample_grade_records)
    assert grouped["Semester 1"] == [88.5, 72.0, 55.0]
