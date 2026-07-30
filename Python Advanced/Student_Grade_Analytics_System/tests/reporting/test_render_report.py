"""Tests for rendering the analytics report as a terminal-friendly report."""

from __future__ import annotations

import pytest

from grade_analytics.models.entities import GradeRecord, Student
from grade_analytics.reporting.build_report import build_analytics_report
from grade_analytics.reporting.render_report import (
    print_analytics_report,
    render_analytics_report,
    render_grade_distribution_table,
    render_major_breakdown_table,
    render_ranking_table,
    render_summary_section,
)


def test_render_summary_section_includes_overall_statistics(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """The summary section reports totals and every overall statistic."""
    report = build_analytics_report(sample_students, sample_grade_records)

    section = render_summary_section(report)

    assert "Total students      : 3" in section
    assert "Total grade records : 5" in section
    assert f"Mean score          : {report['overall_statistics']['mean']}" in section


def test_render_grade_distribution_table_has_a_row_per_grade(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """Every letter grade present in the data gets its own table row."""
    report = build_analytics_report(sample_students, sample_grade_records)

    table = render_grade_distribution_table(report)

    for entry in report["grade_distribution"]:
        assert entry["letter_grade"] in table
        assert f"{entry['percentage']:.2f}%" in table


def test_render_grade_distribution_table_bar_scales_with_percentage(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """A 100% grade share renders a fully-filled 24-character block bar."""
    report = build_analytics_report(sample_students, sample_grade_records)
    report["grade_distribution"] = [
        {"letter_grade": "A", "count": 5, "percentage": 100.0},
    ]

    table = render_grade_distribution_table(report)

    assert "█" * 24 in table


def test_render_ranking_table_lists_every_entry(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """Every ranking entry appears in its own row, in order."""
    report = build_analytics_report(sample_students, sample_grade_records)

    table = render_ranking_table(report["full_ranking"], "FULL RANKING")

    assert table.startswith("FULL RANKING")
    for entry in report["full_ranking"]:
        assert entry["name"] in table


def test_render_major_breakdown_table_lists_every_major(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """Every major appears in the breakdown table."""
    report = build_analytics_report(sample_students, sample_grade_records)

    table = render_major_breakdown_table(report)

    for entry in report["major_breakdown"]:
        assert entry["major"] in table


def test_render_analytics_report_includes_every_section(
    sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """The full report includes the banner and every section heading."""
    report = build_analytics_report(sample_students, sample_grade_records)

    full_report = render_analytics_report(report)

    assert "STUDENT GRADE ANALYTICS REPORT" in full_report
    assert "SUMMARY" in full_report
    assert "GRADE DISTRIBUTION" in full_report
    assert "TOP PERFORMERS" in full_report
    assert "MAJOR BREAKDOWN" in full_report


def test_print_analytics_report_writes_to_stdout(
    sample_students: list[Student],
    sample_grade_records: list[GradeRecord],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """print_analytics_report writes the rendered report to stdout."""
    report = build_analytics_report(sample_students, sample_grade_records)

    print_analytics_report(report)

    assert "STUDENT GRADE ANALYTICS REPORT" in capsys.readouterr().out
