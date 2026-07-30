"""Descriptive statistics and ranking calculations over student scores."""

from __future__ import annotations

import statistics
from collections import Counter

from grade_analytics.models.entities import RankedStudent, Student


def calculate_mean(values: list[float]) -> float:
    """Return the arithmetic mean of ``values``."""
    if not values:
        raise ValueError("Cannot calculate the mean of an empty list")
    return statistics.mean(values)


def calculate_median(values: list[float]) -> float:
    """Return the median of ``values``."""
    if not values:
        raise ValueError("Cannot calculate the median of an empty list")
    return statistics.median(values)


def calculate_mode(values: list[float]) -> list[float]:
    """Return every value tied for the highest frequency; empty if no value repeats."""
    if not values:
        raise ValueError("Cannot calculate the mode of an empty list")
    counts = Counter(values)
    highest_count = max(counts.values())
    if highest_count == 1:
        return []
    return sorted(value for value, count in counts.items() if count == highest_count)


def calculate_percentile_rank(value: float, values: list[float]) -> float:
    """Return the percentage of ``values`` that are less than or equal to ``value``."""
    if not values:
        raise ValueError("Cannot calculate a percentile rank against an empty list")
    at_or_below = sum(1 for other in values if other <= value)
    return (at_or_below / len(values)) * 100.0


def find_highest_score(values: list[float]) -> float | None:
    """Return the highest score in ``values``, or ``None`` if empty."""
    return max(values) if values else None


def find_lowest_score(values: list[float]) -> float | None:
    """Return the lowest score in ``values``, or ``None`` if empty."""
    return min(values) if values else None


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
    averaged.sort(key=lambda pair: pair[1], reverse=True)

    ranked: list[RankedStudent] = []
    previous_average: float | None = None
    current_rank = 0
    for position, (student, average) in enumerate(averaged, start=1):
        if average != previous_average:
            current_rank = position
        ranked.append(RankedStudent(rank=current_rank, student=student, average_score=average))
        previous_average = average
    return ranked
