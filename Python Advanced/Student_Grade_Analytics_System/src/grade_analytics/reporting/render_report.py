"""Render the analytics report as a professional terminal report.

Tables use plain ASCII (``+``, ``-``, ``|``) rather than Unicode box-drawing
characters, since the legacy code page many Windows consoles still default
to cannot display the latter reliably. The distribution bar uses the
Unicode block characters ``█``/``░``, which render correctly on UTF-8
terminals (Windows Terminal, VS Code's integrated terminal).
"""

from __future__ import annotations

from grade_analytics.reporting.build_report import AnalyticsReport, RankingEntry

_BANNER_WIDTH = 78
_BAR_WIDTH = 24


def _build_ascii_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render ``headers``/``rows`` as a bordered ASCII table."""
    column_count = len(headers)
    widths = [
        max(len(str(row[column])) for row in ([headers] + rows)) for column in range(column_count)
    ]
    separator = "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    def _format_row(cells: list[str]) -> str:
        return (
            "|"
            + "|".join(f" {cell:<{width}} " for cell, width in zip(cells, widths, strict=True))
            + "|"
        )

    lines = [separator, _format_row(headers), separator]
    lines.extend(_format_row(row) for row in rows)
    lines.append(separator)
    return "\n".join(lines)


def _build_distribution_bar(percentage: float) -> str:
    """Render ``percentage`` (0-100) as a fixed-width Unicode block bar."""
    filled = round(percentage / 100 * _BAR_WIDTH)
    return "█" * filled + "░" * (_BAR_WIDTH - filled)


def render_summary_section(report: AnalyticsReport) -> str:
    """Render the headline totals and overall statistics."""
    stats = report["overall_statistics"]
    lines = [
        "SUMMARY",
        f"  Total students      : {report['total_students']}",
        f"  Total grade records : {report['total_grade_records']}",
        f"  Mean score          : {stats['mean']}",
        f"  Median score        : {stats['median']}",
        f"  Mode                : {stats['mode']}",
        f"  Highest score       : {stats['highest']}",
        f"  Lowest score        : {stats['lowest']}",
    ]
    return "\n".join(lines)


def render_grade_distribution_table(report: AnalyticsReport) -> str:
    """Render the grade distribution as a table with an inline ASCII bar chart."""
    headers = ["Grade", "Count", "Percentage", "Distribution"]
    rows = [
        [
            entry["letter_grade"],
            str(entry["count"]),
            f"{entry['percentage']:.2f}%",
            _build_distribution_bar(entry["percentage"]),
        ]
        for entry in report["grade_distribution"]
    ]
    return "GRADE DISTRIBUTION\n" + _build_ascii_table(headers, rows)


def render_ranking_table(entries: list[RankingEntry], heading: str) -> str:
    """Render a list of ranking entries as a table under ``heading``."""
    headers = ["Rank", "Name", "Major", "Average Score"]
    rows = [
        [str(entry["rank"]), entry["name"], entry["major"], str(entry["average_score"])]
        for entry in entries
    ]
    return f"{heading}\n" + _build_ascii_table(headers, rows)


def render_major_breakdown_table(report: AnalyticsReport) -> str:
    """Render the per-major aggregate performance as a table."""
    headers = ["Major", "Student Count", "Average Score"]
    rows = [
        [entry["major"], str(entry["student_count"]), str(entry["average_score"])]
        for entry in report["major_breakdown"]
    ]
    return "MAJOR BREAKDOWN\n" + _build_ascii_table(headers, rows)


def render_analytics_report(report: AnalyticsReport) -> str:
    """Render the full analytics report as a professional terminal report."""
    banner = "=" * _BANNER_WIDTH
    sections = [
        banner,
        "STUDENT GRADE ANALYTICS REPORT".center(_BANNER_WIDTH),
        f"Generated: {report['generated_at']}".center(_BANNER_WIDTH),
        banner,
        "",
        render_summary_section(report),
        "",
        render_grade_distribution_table(report),
        "",
        render_ranking_table(report["top_performers"], "TOP PERFORMERS"),
        "",
        render_major_breakdown_table(report),
    ]
    return "\n".join(sections)


def print_analytics_report(report: AnalyticsReport) -> None:
    """Print the full analytics report to stdout."""
    print(render_analytics_report(report))
