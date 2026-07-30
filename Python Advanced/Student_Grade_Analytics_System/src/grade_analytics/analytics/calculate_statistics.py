"""Descriptive statistics and ranking calculations over student scores."""

from __future__ import annotations

import statistics
from collections import Counter

from grade_analytics.models.entities import RankedStudent, Student


def calculate_mean(scores: list[float]) -> float:
    """Return the arithmetic mean of ``scores``."""
    if not scores:
        raise ValueError("Cannot calculate the mean of an empty list")
    return statistics.mean(scores)


def calculate_median(scores: list[float]) -> float:
    """Return the median of ``scores``."""
    if not scores:
        raise ValueError("Cannot calculate the median of an empty list")
    return statistics.median(scores)


def calculate_mode(scores: list[float]) -> list[float]:
    """Return every score tied for the highest frequency; empty if no score repeats."""
    if not scores:
        raise ValueError("Cannot calculate the mode of an empty list")
    score_counts = Counter(scores)
    highest_count = max(score_counts.values())
    if highest_count == 1:
        return []
    return sorted(score for score, count in score_counts.items() if count == highest_count)


def calculate_percentile_rank(score: float, scores: list[float]) -> float:
    """Return the percentage of ``scores`` that are less than or equal to ``score``."""
    if not scores:
        raise ValueError("Cannot calculate a percentile rank against an empty list")
    scores_at_or_below = sum(1 for other_score in scores if other_score <= score)
    return (scores_at_or_below / len(scores)) * 100.0


def find_highest_score(scores: list[float]) -> float | None:
    """Return the highest score in ``scores``, or ``None`` if empty."""
    return max(scores) if scores else None


def find_lowest_score(scores: list[float]) -> float | None:
    """Return the lowest score in ``scores``, or ``None`` if empty."""
    return min(scores) if scores else None


def rank_students_by_average(
    students: list[Student], scores_by_student: dict[str, list[float]]
) -> list[RankedStudent]:
    """Rank ``students`` by descending average score.

    Uses standard competition ranking: students tied on average score share
    the same rank, and the next distinct rank skips ahead accordingly
    (e.g. 1, 2, 2, 4).
    """
    averaged = [
        (student, calculate_mean(scores_by_student[student.student_id]))
        for student in students
        if scores_by_student.get(student.student_id)
    ]
    averaged.sort(key=lambda student_average_pair: student_average_pair[1], reverse=True)

    ranked: list[RankedStudent] = []
    previous_average: float | None = None
    current_rank = 0
    for position, (student, average) in enumerate(averaged, start=1):
        if average != previous_average:
            current_rank = position
        ranked.append(RankedStudent(rank=current_rank, student=student, average_score=average))
        previous_average = average
    return ranked
