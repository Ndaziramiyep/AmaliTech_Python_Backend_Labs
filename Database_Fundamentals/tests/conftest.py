"""Shared pytest fixtures for the social platform test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

SAMPLE_CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
def sample_created_at() -> datetime:
    """A fixed timestamp so entity comparisons in tests are deterministic."""
    return SAMPLE_CREATED_AT
