"""Tests for assembling the TypedDict analytics report."""

from __future__ import annotations

from datetime import datetime

from grade_analytics.models.entities import GradeRecord, Student
from grade_analytics.reporting.build_report import (
    build_analytics_report,
    build_grade_distribution_section,
    build_module_breakdown_section,
    build_rankings_by_group,
)


def test_build_grade_distribution_section_sums_to_full_percentage(
    sample_grade_records: list[GradeRecord],
) -> None:
    """Percentages across every grade bucket add up to 100%."""
    section = build_grade_distribution_section(sample_grade_records)
    assert round(sum(entry["percentage"] for entry in section), 2) == 100.0


def test_build_grade_distribution_section_of_empty_records_is_empty() -> None:
    """No records means no distribution entries."""
    assert build_grade_distribution_section([]) == []


def test_build_module_breakdown_section_groups_by_module(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """Each module appears once with its student count and average score."""
    scores_by_student = {"S001": [88.5, 93.5], "S002": [72.0, 79.5], "S003": [55.0]}
    section = build_module_breakdown_section(sample_students, scores_by_student)
    modules = {entry["module"]: entry for entry in section}
    assert modules["Computer Science"]["student_count"] == 2
    assert modules["Mathematics"]["average_score"] == 55.0


def test_build_module_breakdown_section_skips_a_module_with_no_scores(
    sample_students: list[Student],
) -> None:
    """A module whose students have no recorded scores is left out of the breakdown."""
    section = build_module_breakdown_section(sample_students, scores_by_student={})
    assert section == []


def test_build_analytics_report_has_expected_totals(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """The assembled report's totals match the input data."""
    report = build_analytics_report(sample_students, sample_grade_records, top_n=2)
    assert report["total_students"] == 3
    assert report["total_grade_records"] == 5
    assert len(report["rankings_by_group"]) == 5
    first_group = report["rankings_by_group"][0]
    assert (first_group["year"], first_group["semester"]) == (1, "Semester 1")
    assert first_group["full_ranking"][0]["student_id"] == "S003"


def test_build_rankings_by_group_ranks_only_within_the_same_group() -> None:
    """Students are ranked only against peers in their own (year, semester) group."""
    students = [
        Student(student_id="S001", name="Alice", module="Computer Science", year=2),
        Student(student_id="S002", name="Bob", module="Computer Science", year=2),
        Student(student_id="S003", name="Cara", module="Mathematics", year=1),
    ]
    records = [
        GradeRecord(student_id="S001", course_code="CS201", semester="Semester 1", score=90.0),
        GradeRecord(student_id="S002", course_code="CS201", semester="Semester 1", score=70.0),
        GradeRecord(student_id="S003", course_code="MATH101", semester="Semester 1", score=50.0),
    ]

    groups = build_rankings_by_group(students, records, top_n=5)

    assert len(groups) == 2
    year_two_group = next(group for group in groups if group["year"] == 2)
    assert [entry["student_id"] for entry in year_two_group["full_ranking"]] == ["S001", "S002"]


def test_build_rankings_by_group_applies_top_n_within_each_group() -> None:
    """top_n truncates each group's top and bottom performers independently of other groups."""
    students = [
        Student(student_id="S001", name="Alice", module="CS", year=1),
        Student(student_id="S002", name="Bob", module="CS", year=1),
        Student(student_id="S003", name="Cara", module="CS", year=1),
    ]
    records = [
        GradeRecord(student_id="S001", course_code="CS101", semester="Semester 1", score=95.0),
        GradeRecord(student_id="S002", course_code="CS101", semester="Semester 1", score=85.0),
        GradeRecord(student_id="S003", course_code="CS101", semester="Semester 1", score=75.0),
    ]

    groups = build_rankings_by_group(students, records, top_n=2)

    assert len(groups[0]["top_performers"]) == 2
    assert len(groups[0]["full_ranking"]) == 3
    assert [entry["student_id"] for entry in groups[0]["bottom_performers"]] == ["S003"]


def test_build_rankings_by_group_ranks_on_the_average_of_every_course_not_one_score() -> None:
    """A student's rank comes from the mean of their courses that semester, not any single score."""
    students = [
        Student(student_id="S001", name="Alice", module="CS", year=1),
        Student(student_id="S002", name="Bob", module="CS", year=1),
    ]
    records = [
        # S001's individual course scores (50.0, 100.0) straddle S002's 74.0 on either
        # side, but their average (75.0) is what should be compared against S002.
        GradeRecord(student_id="S001", course_code="CS101", semester="Semester 1", score=50.0),
        GradeRecord(student_id="S001", course_code="CS102", semester="Semester 1", score=100.0),
        GradeRecord(student_id="S002", course_code="CS101", semester="Semester 1", score=74.0),
    ]

    ranking = build_rankings_by_group(students, records, top_n=5)[0]["full_ranking"]

    assert [entry["student_id"] for entry in ranking] == ["S001", "S002"]
    assert ranking[0]["average_score"] == 75.0


def test_build_rankings_by_group_records_a_score_per_course() -> None:
    """Each entry's ``course_scores`` carries its own score for every course the group shares."""
    students = [
        Student(student_id="S001", name="Alice", module="CSC", year=2),
        Student(student_id="S002", name="Bob", module="Math", year=2),
    ]
    records = [
        GradeRecord(student_id="S001", course_code="CSC", semester="Semester 1", score=88.5),
        GradeRecord(student_id="S001", course_code="Math", semester="Semester 1", score=91.0),
        GradeRecord(student_id="S002", course_code="CSC", semester="Semester 1", score=59.5),
        GradeRecord(student_id="S002", course_code="Math", semester="Semester 1", score=63.0),
    ]

    group = build_rankings_by_group(students, records, top_n=5)[0]

    assert group["courses"] == ["CSC", "Math"]
    alice = next(entry for entry in group["full_ranking"] if entry["student_id"] == "S001")
    assert alice["course_scores"] == {"CSC": 88.5, "Math": 91.0}


def test_build_analytics_report_generated_at_is_iso_timestamp(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """generated_at is an ISO-8601 formatted timestamp string."""
    report = build_analytics_report(sample_students, sample_grade_records)
    datetime.fromisoformat(report["generated_at"])
