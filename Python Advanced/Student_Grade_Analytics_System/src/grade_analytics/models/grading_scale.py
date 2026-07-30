"""Conversion between numeric scores and letter grades."""

from __future__ import annotations

_SCALE: tuple[tuple[float, str], ...] = (
    (90.0, "A"),
    (80.0, "B"),
    (70.0, "C"),
    (60.0, "D"),
)
_FAILING_GRADE = "F"


def convert_score_to_letter_grade(score: float) -> str:
    """Convert a numeric ``score`` (0-100) to its letter grade."""
    for threshold, letter_grade in _SCALE:
        if score >= threshold:
            return letter_grade
    return _FAILING_GRADE
