"""Write the analytics report to ``grade_report.json``, and read it back from there."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from grade_analytics.models.exceptions import (
    StudentDataFileNotFoundError,
    StudentDataFilePermissionError,
)
from grade_analytics.reporting.build_report import AnalyticsReport

# Default location of the JSON report this module reads and writes.
report_json_path = Path("reports/grade_report.json")


def write_report_to_json(report: AnalyticsReport, path: Path | str = report_json_path) -> None:
    """Write ``report`` to ``path`` as formatted JSON (write access), creating parent dirs."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(report, json_file, indent=2)
    except PermissionError as exc:
        raise StudentDataFilePermissionError(f"Cannot write report to: {output_path}") from exc


def load_report_from_json(path: Path | str = report_json_path) -> AnalyticsReport:
    """Read the JSON report back from ``path`` (read access)."""
    input_path = Path(path)
    try:
        with open(input_path, encoding="utf-8") as json_file:
            return cast(AnalyticsReport, json.load(json_file))
    except FileNotFoundError as exc:
        raise StudentDataFileNotFoundError(f"Report file not found: {input_path}") from exc
    except PermissionError as exc:
        raise StudentDataFilePermissionError(f"Cannot read report from: {input_path}") from exc
