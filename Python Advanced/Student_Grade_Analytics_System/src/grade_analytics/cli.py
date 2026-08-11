"""Command-line entry point that ties the analytics pipeline together."""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from grade_analytics.file_io.load_students import (
    csv_file_path,
    load_grade_records_from_csv,
    load_students_from_csv,
)
from grade_analytics.file_io.write_report import (
    load_report_from_json,
    report_json_path,
    write_report_to_json,
)
from grade_analytics.models.exceptions import StudentDataError
from grade_analytics.reporting.build_report import AnalyticsReport, build_analytics_report
from grade_analytics.reporting.render_report import print_analytics_report


def parse_command_line_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the analytics tool."""
    parser = argparse.ArgumentParser(description="Student Grade Analytics Tool")
    parser.add_argument(
        "--input", type=Path, default=csv_file_path, help="Path to the input CSV file (read)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=report_json_path,
        help="Path to write the JSON report to, then read it back from (write, then read)",
    )
    parser.add_argument("--top-n", type=int, default=5, help="Number of top performers to include")
    return parser.parse_args(argv)


def run_analytics_pipeline(input_path: Path, output_path: Path, top_n: int) -> AnalyticsReport:
    """Read ``input_path`` CSV, write the report to ``output_path`` JSON, then read it back.

    Reading the report back from ``output_path`` (instead of reusing the
    in-memory copy) guarantees the CLI displays exactly what was saved.
    """
    students = load_students_from_csv(input_path)  # read access: input_path
    records = load_grade_records_from_csv(input_path)  # read access: input_path
    report = build_analytics_report(students, records, top_n=top_n)
    write_report_to_json(report, output_path)  # write access: output_path
    return load_report_from_json(output_path)  # read access: output_path


def _ensure_utf8_stdout(stream: object) -> None:
    """Reconfigure ``stream`` to UTF-8 if it's a real stdout stream using another encoding.

    The report's distribution bars use Unicode block characters, which
    Windows' legacy console code pages (e.g. cp1252) can't encode.
    """
    if isinstance(stream, io.TextIOWrapper) and stream.encoding.lower() not in {"utf-8", "utf8"}:
        stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> None:
    """Run the CLI: build the report, write it to JSON, and print it back from that file."""
    _ensure_utf8_stdout(sys.stdout)
    args = parse_command_line_arguments(argv)
    try:
        report = run_analytics_pipeline(args.input, args.output, args.top_n)
    except StudentDataError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print_analytics_report(report)  # report content read from args.output
    print(f"\nReport written to {args.output}")


if __name__ == "__main__":
    main()
