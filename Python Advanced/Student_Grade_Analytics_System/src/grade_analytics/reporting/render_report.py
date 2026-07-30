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


def _build_ascii_table(table_headers: list[str], table_rows: list[list[str]]) -> str:
    """Render ``table_headers``/``table_rows`` as a bordered ASCII table."""
    column_count = len(table_headers)
    column_widths = [
        max(len(str(table_row[column_index])) for table_row in ([table_headers] + table_rows))
        for column_index in range(column_count)
    ]
    border_line = "+" + "+".join("-" * (column_width + 2) for column_width in column_widths) + "+"

    def _format_table_row(row_cells: list[str]) -> str:
        return (
            "|"
            + "|".join(
                f" {cell:<{column_width}} "
                for cell, column_width in zip(row_cells, column_widths, strict=True)
            )
            + "|"
        )

    table_lines = [border_line, _format_table_row(table_headers), border_line]
    table_lines.extend(_format_table_row(table_row) for table_row in table_rows)
    table_lines.append(border_line)
    return "\n".join(table_lines)


def _build_distribution_bar(percentage: float) -> str:
    """Render ``percentage`` (0-100) as a fixed-width Unicode block bar."""
    filled_block_count = round(percentage / 100 * _BAR_WIDTH)
    return "█" * filled_block_count + "░" * (_BAR_WIDTH - filled_block_count)


def _format_mode_values(mode_values: list[float]) -> str:
    """Format the mode(s) for display: none if no score repeats, else every tied score."""
    if not mode_values:
        return "No mode"
    return ", ".join(str(mode_value) for mode_value in mode_values)


def render_summary_section(report: AnalyticsReport) -> str:
    """Render the headline totals and overall statistics."""
    overall_statistics = report["overall_statistics"]
    summary_lines = [
        "SUMMARY",
        f"  Total students      : {report['total_students']}",
        f"  Total grade records : {report['total_grade_records']}",
        f"  Mean score          : {overall_statistics['mean']}",
        f"  Median score        : {overall_statistics['median']}",
        f"  Mode                : {_format_mode_values(overall_statistics['mode'])}",
        f"  Highest score       : {overall_statistics['highest']}",
        f"  Lowest score        : {overall_statistics['lowest']}",
    ]
    return "\n".join(summary_lines)


def render_grade_distribution_table(report: AnalyticsReport) -> str:
    """Render the grade distribution as a table with an inline ASCII bar chart."""
    table_headers = ["Grade", "Count", "Percentage", "Distribution"]
    table_rows = [
        [
            distribution_entry["letter_grade"],
            str(distribution_entry["count"]),
            f"{distribution_entry['percentage']:.2f}%",
            _build_distribution_bar(distribution_entry["percentage"]),
        ]
        for distribution_entry in report["grade_distribution"]
    ]
    return "GRADE DISTRIBUTION\n" + _build_ascii_table(table_headers, table_rows)


def render_ranking_table(ranking_entries: list[RankingEntry], heading: str) -> str:
    """Render a list of ranking entries as a table under ``heading``."""
    table_headers = ["Rank", "Name", "Major", "Average Score"]
    table_rows = [
        [
            str(ranking_entry["rank"]),
            ranking_entry["name"],
            ranking_entry["major"],
            str(ranking_entry["average_score"]),
        ]
        for ranking_entry in ranking_entries
    ]
    return f"{heading}\n" + _build_ascii_table(table_headers, table_rows)


def render_major_breakdown_table(report: AnalyticsReport) -> str:
    """Render the per-major aggregate performance as a table."""
    table_headers = ["Major", "Student Count", "Average Score"]
    table_rows = [
        [
            breakdown_entry["major"],
            str(breakdown_entry["student_count"]),
            str(breakdown_entry["average_score"]),
        ]
        for breakdown_entry in report["major_breakdown"]
    ]
    return "MAJOR BREAKDOWN\n" + _build_ascii_table(table_headers, table_rows)


def render_analytics_report(report: AnalyticsReport) -> str:
    """Render the full analytics report as a professional terminal report."""
    banner = "=" * _BANNER_WIDTH
    report_sections = [
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
    return "\n".join(report_sections)


def print_analytics_report(report: AnalyticsReport) -> None:
    """Print the full analytics report to stdout."""
    print(render_analytics_report(report))
