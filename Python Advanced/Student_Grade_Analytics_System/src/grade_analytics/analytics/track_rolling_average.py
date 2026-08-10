"""Rolling-average tracking backed by a fixed-size ``deque``."""

from __future__ import annotations

from collections import deque


class RollingAverageTracker:
    """Tracks the average of the most recent ``window_size`` scores."""

    def __init__(self, window_size: int) -> None:
        if window_size < 1:
            raise ValueError("window_size must be at least 1")
        self._scores: deque[float] = deque(maxlen=window_size)

    def add_score(self, score: float) -> None:
        """Record a new ``score``, evicting the oldest if the window is full."""
        self._scores.append(score)

    def get_current_average(self) -> float | None:
        """Return the average of scores currently in the window, or ``None``."""
        if not self._scores:
            return None
        return sum(self._scores) / len(self._scores)

    def get_history(self) -> list[float]:
        """Return the scores currently held in the window, oldest first."""
        return list(self._scores)


def track_semester_trend(scores: list[float], window_size: int) -> list[float]:
    """Return one rolling average per score in ``scores``, over a ``window_size`` window."""
    tracker = RollingAverageTracker(window_size)
    trend: list[float] = []
    for score in scores:
        tracker.add_score(score)
        average = tracker.get_current_average()
        assert average is not None  # at least one score was just added
        trend.append(average)
    return trend
