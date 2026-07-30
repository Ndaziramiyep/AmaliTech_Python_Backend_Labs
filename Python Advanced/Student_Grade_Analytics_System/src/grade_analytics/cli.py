"""Command-line entry point that ties the analytics pipeline together."""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from grade_analytics.file_io.load_students import (
    load_grade_records_from_csv,
    load_students_from_csv,
)
from grade_analytics.file_io.write_report import write_report_to_json
from grade_analytics.models.exceptions import StudentDataError
from grade_analytics.reporting.build_report import AnalyticsReport, build_analytics_report
from grade_analytics.reporting.render_report import print_analytics_report
from grade_analytics.reporting.visualize_report import generate_all_visualizations

_DEFAULT_INPUT = Path("data/sample_students.csv")
_DEFAULT_OUTPUT = Path("reports/grade_report.json")
_DEFAULT_CHARTS_DIR = Path("reports/charts")


def parse_command_line_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the analytics tool."""
    parser = argparse.ArgumentParser(description="Student Grade Analytics Tool")
    parser.add_argument(
        "--input", type=Path, default=_DEFAULT_INPUT, help="Path to the input CSV file"
    )
    parser.add_argument(
        "--output", type=Path, default=_DEFAULT_OUTPUT, help="Path to write the JSON report to"
    )
    parser.add_argument("--top-n", type=int, default=5, help="Number of top performers to include")
    parser.add_argument(
        "--visualize", action="store_true", help="Also render PNG chart visualizations"
    )
    parser.add_argument(
        "--charts-dir",
        type=Path,
        default=_DEFAULT_CHARTS_DIR,
        help="Directory to write chart PNGs to (with --visualize)",
    )
    return parser.parse_args(argv)


def run_analytics_pipeline(input_path: Path, output_path: Path, top_n: int) -> AnalyticsReport:
    """Load ``input_path``, build the analytics report, and write it to ``output_path``."""
    students = load_students_from_csv(input_path)
    records = load_grade_records_from_csv(input_path)
    report = build_analytics_report(students, records, top_n=top_n)
    write_report_to_json(report, output_path)
    return report


def main(argv: list[str] | None = None) -> None:
    """Run the CLI: parse arguments, build the report, and print it."""
    # The report's distribution bars use Unicode block characters, which
    # Windows' legacy console code pages (e.g. cp1252) can't encode.
    if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding.lower() not in {
        "utf-8",
        "utf8",
    }:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_command_line_arguments(argv)
    try:
        report = run_analytics_pipeline(args.input, args.output, args.top_n)
    except StudentDataError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print_analytics_report(report)
    print(f"\nReport written to {args.output}")

    if args.visualize:
        chart_paths = generate_all_visualizations(report, args.charts_dir)
        for chart_path in chart_paths:
            print(f"Chart written to {chart_path}")


if __name__ == "__main__":
    main()
