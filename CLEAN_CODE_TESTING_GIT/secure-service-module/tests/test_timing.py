"""Tests for the operation-timing context manager used by UserService."""

import logging

import pytest

from src.auth.service import _timed_operation


def test_timed_operation_logs_start_and_finish_with_duration(caplog):
    """Entering and exiting the context manager logs start/finish debug events."""
    with caplog.at_level(logging.DEBUG):
        with _timed_operation("unit_test_op") as timer:
            assert timer.elapsed_ms >= 0

    messages = [record.message for record in caplog.records]
    assert any("unit_test_op started" in message for message in messages)

    finish_records = [r for r in caplog.records if "unit_test_op finished" in r.message]
    assert len(finish_records) == 1
    assert finish_records[0].duration_ms >= 0


def test_timed_operation_reraises_exceptions_and_still_logs_finish(caplog):
    """An exception raised inside the block propagates, and finish is still logged."""
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ValueError):
            with _timed_operation("failing_op"):
                raise ValueError("boom")

    finish_records = [r for r in caplog.records if "failing_op finished" in r.message]
    assert len(finish_records) == 1
