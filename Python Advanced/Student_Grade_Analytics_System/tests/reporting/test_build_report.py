"""Tests for assembling the TypedDict analytics report."""

from __future__ import annotations

from datetime import datetime

from grade_analytics.models.entities import GradeRecord, Student
from grade_analytics.reporting.build_report import (
    build_analytics_report,
    build_grade_distribution_section,
    build_major_breakdown_section,
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


def test_build_major_breakdown_section_groups_by_major(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """Each major appears once with its student count and average score."""
    scores_by_student = {"S001": [88.5, 93.5], "S002": [72.0, 79.5], "S003": [55.0]}
    section = build_major_breakdown_section(sample_students, scores_by_student)
    majors = {entry["major"]: entry for entry in section}
    assert majors["Computer Science"]["student_count"] == 2
    assert majors["Mathematics"]["average_score"] == 55.0


def test_build_analytics_report_has_expected_totals(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """The assembled report's totals match the input data."""
    report = build_analytics_report(sample_students, sample_grade_records, top_n=2)
    assert report["total_students"] == 3
    assert report["total_grade_records"] == 5
    assert len(report["top_performers"]) == 2
    assert len(report["full_ranking"]) == 3
    assert report["full_ranking"][0]["student_id"] == "S001"


def test_build_analytics_report_generated_at_is_iso_timestamp(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """generated_at is an ISO-8601 formatted timestamp string."""
    report = build_analytics_report(sample_students, sample_grade_records)
    datetime.fromisoformat(report["generated_at"])
