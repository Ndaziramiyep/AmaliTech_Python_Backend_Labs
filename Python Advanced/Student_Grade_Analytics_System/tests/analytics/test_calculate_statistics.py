"""Tests for descriptive statistics and student ranking."""

from __future__ import annotations

import pytest

from grade_analytics.analytics.calculate_statistics import (
    calculate_mean,
    calculate_median,
    calculate_mode,
    calculate_percentile_rank,
    find_highest_score,
    find_lowest_score,
    rank_students_by_average,
)
from grade_analytics.models.entities import Student


def test_calculate_mean_of_known_values() -> None:
    """The mean of a known set of values matches the expected result."""
    assert calculate_mean([60.0, 80.0, 100.0]) == 80.0


def test_calculate_mean_rejects_empty_list() -> None:
    """An empty list has no mean."""
    with pytest.raises(ValueError):
        calculate_mean([])


def test_calculate_median_of_odd_length_list() -> None:
    """The median of an odd-length list is its middle value."""
    assert calculate_median([70.0, 90.0, 80.0]) == 80.0


def test_calculate_mode_returns_single_most_frequent_value() -> None:
    """When exactly one value repeats the most, it is the sole mode."""
    assert calculate_mode([70.0, 70.0, 70.0, 90.0, 55.0]) == [70.0]


def test_calculate_mode_returns_every_tied_value() -> None:
    """When multiple values share the highest frequency, all of them are modes."""
    assert calculate_mode([70.0, 70.0, 90.0, 90.0, 55.0]) == [70.0, 90.0]


def test_calculate_mode_returns_empty_when_no_value_repeats() -> None:
    """When every value is unique, there is no mode."""
    assert calculate_mode([70.0, 80.0, 90.0]) == []


def test_calculate_percentile_rank_of_median_value() -> None:
    """A value at the middle of a sorted list sits around the 50th percentile."""
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert calculate_percentile_rank(30.0, values) == 60.0


def test_find_highest_and_lowest_score() -> None:
    """The highest and lowest of a list of scores are found correctly."""
    values = [55.0, 90.0, 72.0]
    assert find_highest_score(values) == 90.0
    assert find_lowest_score(values) == 55.0


def test_find_highest_score_of_empty_list_is_none() -> None:
    """An empty list has no highest score."""
    assert find_highest_score([]) is None


def test_rank_students_by_average_orders_descending(sample_students: list[Student]) -> None:
    """Students are ranked from highest to lowest average score."""
    scores_by_student = {"S001": [90.0], "S002": [70.0], "S003": [80.0]}
    ranking = rank_students_by_average(sample_students, scores_by_student)
    assert [entry.student.student_id for entry in ranking] == ["S001", "S003", "S002"]
    assert [entry.rank for entry in ranking] == [1, 2, 3]


def test_rank_students_by_average_gives_tied_students_the_same_rank(
    sample_students: list[Student],
) -> None:
    """Tied average scores share a rank, and the next rank skips ahead."""
    scores_by_student = {"S001": [90.0], "S002": [90.0], "S003": [80.0]}
    ranking = rank_students_by_average(sample_students, scores_by_student)
    ranks_by_id = {entry.student.student_id: entry.rank for entry in ranking}
    assert ranks_by_id["S001"] == ranks_by_id["S002"] == 1
    assert ranks_by_id["S003"] == 3


def test_rank_students_by_average_skips_students_with_no_scores(
    sample_students: list[Student],
) -> None:
    """A student with no recorded scores is excluded from the ranking."""
    scores_by_student = {"S001": [90.0], "S003": [80.0]}
    ranking = rank_students_by_average(sample_students, scores_by_student)
    assert {entry.student.student_id for entry in ranking} == {"S001", "S003"}
