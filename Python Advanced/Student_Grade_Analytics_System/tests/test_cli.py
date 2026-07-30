"""Tests for the command-line entry point."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from grade_analytics.cli import main, parse_command_line_arguments, run_analytics_pipeline
from grade_analytics.models.exceptions import StudentDataError
from grade_analytics.reporting.render_report import print_analytics_report


def test_parse_command_line_arguments_uses_defaults_when_omitted() -> None:
    """With no arguments, the defaults for input, output, and top-n apply."""
    args = parse_command_line_arguments([])
    assert args.input == Path("data/sample_students.csv")
    assert args.output == Path("reports/grade_report.json")
    assert args.top_n == 5


def test_parse_command_line_arguments_honors_overrides() -> None:
    """Explicit --input/--output/--top-n values override the defaults."""
    args = parse_command_line_arguments(
        ["--input", "custom.csv", "--output", "out.json", "--top-n", "3"]
    )
    assert args.input == Path("custom.csv")
    assert args.output == Path("out.json")
    assert args.top_n == 3


def test_parse_command_line_arguments_visualize_defaults_to_off() -> None:
    """--visualize is opt-in; charts are not generated unless requested."""
    args = parse_command_line_arguments([])
    assert args.visualize is False
    assert args.charts_dir == Path("reports/charts")


def test_main_writes_charts_when_visualize_flag_is_set(
    sample_csv_file: Path, tmp_path: Path
) -> None:
    """Passing --visualize renders chart PNGs alongside the JSON report."""
    charts_dir = tmp_path / "charts"
    main(
        [
            "--input",
            str(sample_csv_file),
            "--output",
            str(tmp_path / "report.json"),
            "--visualize",
            "--charts-dir",
            str(charts_dir),
        ]
    )

    assert list(charts_dir.glob("*.png"))


def test_run_analytics_pipeline_writes_report_file(sample_csv_file: Path, tmp_path: Path) -> None:
    """Running the pipeline end-to-end produces a JSON report on disk."""
    output_path = tmp_path / "report.json"

    report = run_analytics_pipeline(sample_csv_file, output_path, top_n=2)

    assert output_path.exists()
    assert report["total_students"] == 3


def test_print_analytics_report_names_top_performer(
    sample_csv_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The printed report names the top-ranked student."""
    report = run_analytics_pipeline(sample_csv_file, tmp_path / "report.json", top_n=2)

    print_analytics_report(report)

    assert "TOP PERFORMERS" in capsys.readouterr().out


def test_main_prints_full_report_to_stdout(
    sample_csv_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Running main() end-to-end prints the full formatted report."""
    main(
        [
            "--input",
            str(sample_csv_file),
            "--output",
            str(tmp_path / "report.json"),
        ]
    )

    output = capsys.readouterr().out
    assert "STUDENT GRADE ANALYTICS REPORT" in output
    assert "GRADE DISTRIBUTION" in output
    assert "MAJOR BREAKDOWN" in output
    assert "Report written to" in output


def test_main_exits_with_status_one_on_student_data_error(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A StudentDataError anywhere in the pipeline becomes a clean SystemExit(1)."""
    mocker.patch(
        "grade_analytics.cli.run_analytics_pipeline",
        side_effect=StudentDataError("boom"),
    )

    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 1
    assert "boom" in capsys.readouterr().err
