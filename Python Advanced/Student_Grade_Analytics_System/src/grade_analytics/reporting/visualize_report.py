"""Render PNG chart visualizations from an analytics report.

Each chart here is a single measure across categories that are already
labeled on their axis (letter grade, student name, major), so a single
consistent hue is used rather than one color per bar -- per-bar color would
be decorative, not identity-bearing, and a multi-hue bar chart with no
legend is a known anti-pattern. The hue and ink tokens below are the
light-mode slots of a colorblind-validated palette. Uses the non-interactive
Agg backend so charts render without a display (e.g. in CI or a headless
test run).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from grade_analytics.reporting.build_report import AnalyticsReport  # noqa: E402

_SURFACE = "#fcfcfb"
_PRIMARY_INK = "#0b0b0b"
_SECONDARY_INK = "#52514e"
_MUTED_INK = "#898781"
_GRIDLINE = "#e1e0d9"
_BASELINE = "#c3c2b7"
_SERIES_1 = "#2a78d6"


def _style_chart_axes(figure: Figure, axes: Axes, title: str, x_label: str, y_label: str) -> None:
    figure.set_facecolor(_SURFACE)
    axes.set_facecolor(_SURFACE)
    axes.set_title(title, color=_PRIMARY_INK, fontsize=12, loc="left")
    axes.set_xlabel(x_label, color=_SECONDARY_INK)
    axes.set_ylabel(y_label, color=_SECONDARY_INK)
    axes.tick_params(colors=_MUTED_INK)
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
    axes.spines["left"].set_color(_BASELINE)
    axes.spines["bottom"].set_color(_BASELINE)
    axes.yaxis.grid(True, color=_GRIDLINE, linewidth=0.8)
    axes.set_axisbelow(True)


def _save_chart_to_png(figure: Figure, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path, facecolor=figure.get_facecolor())
    plt.close(figure)
    return output_path


def plot_grade_distribution(report: AnalyticsReport, output_path: Path) -> Path:
    """Render a bar chart of letter grade counts to ``output_path`` (PNG)."""
    distribution = report["grade_distribution"]
    figure, axes = plt.subplots(figsize=(6, 4))
    axes.bar(
        [entry["letter_grade"] for entry in distribution],
        [entry["count"] for entry in distribution],
        color=_SERIES_1,
    )
    _style_chart_axes(figure, axes, "Grade Distribution", "Letter Grade", "Number of Records")
    return _save_chart_to_png(figure, output_path)


def plot_top_performers(report: AnalyticsReport, output_path: Path) -> Path:
    """Render a horizontal bar chart of the top performers' average scores."""
    top_performers = list(reversed(report["top_performers"]))
    figure, axes = plt.subplots(figsize=(6, 4))
    axes.barh(
        [entry["name"] for entry in top_performers],
        [entry["average_score"] for entry in top_performers],
        color=_SERIES_1,
    )
    _style_chart_axes(figure, axes, "Top Performers", "Average Score", "")
    return _save_chart_to_png(figure, output_path)


def plot_major_breakdown(report: AnalyticsReport, output_path: Path) -> Path:
    """Render a bar chart of average score by major."""
    breakdown = report["major_breakdown"]
    figure, axes = plt.subplots(figsize=(6, 4))
    axes.bar(
        [entry["major"] for entry in breakdown],
        [entry["average_score"] for entry in breakdown],
        color=_SERIES_1,
    )
    axes.tick_params(axis="x", rotation=20)
    _style_chart_axes(figure, axes, "Average Score by Major", "", "Average Score")
    return _save_chart_to_png(figure, output_path)


def generate_all_visualizations(report: AnalyticsReport, output_dir: Path) -> list[Path]:
    """Render every chart for ``report`` into ``output_dir``, returning the files written."""
    return [
        plot_grade_distribution(report, output_dir / "grade_distribution.png"),
        plot_top_performers(report, output_dir / "top_performers.png"),
        plot_major_breakdown(report, output_dir / "major_breakdown.png"),
    ]
