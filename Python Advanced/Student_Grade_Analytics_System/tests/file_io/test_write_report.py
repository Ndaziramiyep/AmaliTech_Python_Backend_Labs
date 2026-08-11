"""Tests for writing the analytics report to a JSON file, and reading it back."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from grade_analytics.file_io.write_report import load_report_from_json, write_report_to_json
from grade_analytics.models.entities import GradeRecord, Student
from grade_analytics.models.exceptions import (
    StudentDataFileNotFoundError,
    StudentDataFilePermissionError,
)
from grade_analytics.reporting.build_report import build_analytics_report


def test_write_report_to_json_produces_readable_file(
    tmp_path: Path, sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """The report is written as valid JSON that round-trips to the same data."""
    report = build_analytics_report(sample_students, sample_grade_records)
    output_path = tmp_path / "report.json"

    write_report_to_json(report, output_path)

    with open(output_path, encoding="utf-8") as json_file:
        loaded = json.load(json_file)
    assert loaded["total_students"] == report["total_students"]


def test_write_report_to_json_creates_missing_parent_directories(
    tmp_path: Path, sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """Parent directories that don't exist yet are created automatically."""
    report = build_analytics_report(sample_students, sample_grade_records)
    output_path = tmp_path / "nested" / "dir" / "report.json"

    write_report_to_json(report, output_path)

    assert output_path.exists()


def test_write_report_to_json_raises_for_permission_error(
    tmp_path: Path,
    sample_students: list[Student],
    sample_grade_records: list[GradeRecord],
    mocker: MockerFixture,
) -> None:
    """A PermissionError while writing is translated to a domain error."""
    report = build_analytics_report(sample_students, sample_grade_records)
    mocker.patch("builtins.open", side_effect=PermissionError)

    with pytest.raises(StudentDataFilePermissionError):
        write_report_to_json(report, tmp_path / "report.json")


def test_load_report_from_json_round_trips_a_written_report(
    tmp_path: Path, sample_students: list[Student], sample_grade_records: list[GradeRecord]
) -> None:
    """A report written to disk reads back with the same data."""
    report = build_analytics_report(sample_students, sample_grade_records)
    output_path = tmp_path / "report.json"
    write_report_to_json(report, output_path)

    loaded = load_report_from_json(output_path)

    assert loaded == report


def test_load_report_from_json_raises_for_missing_file(tmp_path: Path) -> None:
    """A missing report path raises the domain-specific not-found error."""
    with pytest.raises(StudentDataFileNotFoundError):
        load_report_from_json(tmp_path / "does_not_exist.json")


def test_load_report_from_json_raises_for_permission_error(
    tmp_path: Path,
    sample_students: list[Student],
    sample_grade_records: list[GradeRecord],
    mocker: MockerFixture,
) -> None:
    """A PermissionError while reading is translated to a domain error."""
    report = build_analytics_report(sample_students, sample_grade_records)
    output_path = tmp_path / "report.json"
    write_report_to_json(report, output_path)
    mocker.patch("builtins.open", side_effect=PermissionError)

    with pytest.raises(StudentDataFilePermissionError):
        load_report_from_json(output_path)
