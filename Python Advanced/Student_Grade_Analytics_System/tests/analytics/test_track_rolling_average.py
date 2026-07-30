"""Tests for the deque-backed rolling average tracker."""

from __future__ import annotations

import pytest

from grade_analytics.analytics.track_rolling_average import (
    RollingAverageTracker,
    track_semester_trend,
)


def test_rolling_average_tracker_rejects_non_positive_window() -> None:
    """A window size below 1 is invalid."""
    with pytest.raises(ValueError):
        RollingAverageTracker(window_size=0)


def test_rolling_average_tracker_returns_none_when_empty() -> None:
    """With no scores added, there is no average yet."""
    tracker = RollingAverageTracker(window_size=3)
    assert tracker.get_current_average() is None


def test_rolling_average_tracker_averages_within_window() -> None:
    """The average reflects only the scores currently in the window."""
    tracker = RollingAverageTracker(window_size=3)
    for score in (60.0, 80.0, 100.0):
        tracker.add_score(score)
    assert tracker.get_current_average() == 80.0


def test_rolling_average_tracker_evicts_oldest_beyond_window() -> None:
    """Once the window is full, the oldest score is dropped on the next add."""
    tracker = RollingAverageTracker(window_size=2)
    tracker.add_score(50.0)
    tracker.add_score(70.0)
    tracker.add_score(90.0)
    assert tracker.get_history() == [70.0, 90.0]
    assert tracker.get_current_average() == 80.0


def test_track_semester_trend_returns_one_average_per_score() -> None:
    """track_semester_trend produces a rolling average aligned to each input score."""
    trend = track_semester_trend([60.0, 80.0, 100.0], window_size=2)
    assert trend == [60.0, 70.0, 90.0]
