"""Persist an :class:`~grade_analytics.reporting.build_report.AnalyticsReport` as JSON."""

from __future__ import annotations

import json
from pathlib import Path

from grade_analytics.models.exceptions import StudentDataFilePermissionError
from grade_analytics.reporting.build_report import AnalyticsReport


def write_report_to_json(report: AnalyticsReport, path: Path | str) -> None:
    """Write ``report`` to ``path`` as formatted JSON, creating parent directories."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(report, json_file, indent=2)
    except PermissionError as exc:
        raise StudentDataFilePermissionError(f"Cannot write report to: {output_path}") from exc
