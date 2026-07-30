"""Tests for PNG chart generation from an analytics report."""

from __future__ import annotations

from pathlib import Path

from grade_analytics.models.entities import GradeRecord, Student
from grade_analytics.reporting.build_report import build_analytics_report
from grade_analytics.reporting.visualize_report import (
    generate_all_visualizations,
    plot_grade_distribution,
    plot_major_breakdown,
    plot_top_performers,
)


def test_plot_grade_distribution_writes_a_non_empty_png(
    tmp_path: Path, sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """The grade distribution chart is written as a non-empty PNG file."""
    report = build_analytics_report(sample_students, sample_grade_records)
    output_path = tmp_path / "grade_distribution.png"

    result_path = plot_grade_distribution(report, output_path)

    assert result_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_top_performers_writes_a_non_empty_png(
    tmp_path: Path, sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """The top-performers chart is written as a non-empty PNG file."""
    report = build_analytics_report(sample_students, sample_grade_records)
    output_path = tmp_path / "top_performers.png"

    plot_top_performers(report, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_major_breakdown_writes_a_non_empty_png(
    tmp_path: Path, sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """The major-breakdown chart is written as a non-empty PNG file."""
    report = build_analytics_report(sample_students, sample_grade_records)
    output_path = tmp_path / "major_breakdown.png"

    plot_major_breakdown(report, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_all_visualizations_writes_every_chart(
    tmp_path: Path, sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """generate_all_visualizations writes one PNG per chart and returns their paths."""
    report = build_analytics_report(sample_students, sample_grade_records)
    charts_dir = tmp_path / "charts"

    chart_paths = generate_all_visualizations(report, charts_dir)

    assert len(chart_paths) == 3
    assert all(path.exists() for path in chart_paths)
