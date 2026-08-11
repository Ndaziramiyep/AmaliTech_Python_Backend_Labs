"""Tests for the command-line entry point."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from grade_analytics.cli import (
    _ensure_utf8_stdout,
    main,
    parse_command_line_arguments,
    run_analytics_pipeline,
)
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


def test_ensure_utf8_stdout_reconfigures_a_non_utf8_text_stream() -> None:
    """A real text stream on a legacy code page (e.g. Windows cp1252) is switched to UTF-8."""
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")

    _ensure_utf8_stdout(stream)

    assert stream.encoding.lower() in {"utf-8", "utf8"}


def test_ensure_utf8_stdout_leaves_a_utf8_text_stream_alone() -> None:
    """A stream already on UTF-8 is left as-is."""
    stream = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")

    _ensure_utf8_stdout(stream)

    assert stream.encoding.lower() in {"utf-8", "utf8"}


def test_ensure_utf8_stdout_ignores_a_non_text_io_wrapper_stream() -> None:
    """A stream that isn't a real TextIOWrapper (e.g. pytest's capsys) is left untouched."""
    _ensure_utf8_stdout(object())


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
    assert "MODULE BREAKDOWN" in output
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
