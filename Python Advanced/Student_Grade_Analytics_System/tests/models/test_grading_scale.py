"""Tests for numeric-score-to-letter-grade conversion."""

from __future__ import annotations

import pytest

from grade_analytics.models.grading_scale import convert_score_to_letter_grade


@pytest.mark.parametrize(
    ("score", "expected_letter"),
    [
        (100.0, "A"),
        (90.0, "A"),
        (89.99, "B"),
        (80.0, "B"),
        (70.0, "C"),
        (60.0, "D"),
        (59.99, "F"),
        (0.0, "F"),
    ],
)
def test_convert_score_to_letter_grade_boundaries(score: float, expected_letter: str) -> None:
    """Each grade boundary maps to the expected letter, inclusive of its lower bound."""
    assert convert_score_to_letter_grade(score) == expected_letter
