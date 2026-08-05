"""Shared fixtures for PostgreSQL repository unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from social_platform.database.postgres_connection_pool import PostgresConnectionPool


@pytest.fixture
def fake_cursor() -> MagicMock:
    """A mock RealDictCursor whose execute/fetchone/fetchall/rowcount tests configure."""
    return MagicMock()


@pytest.fixture
def fake_connection_pool(fake_cursor: MagicMock) -> MagicMock:
    """A mock PostgresConnectionPool whose cursor() context manager yields `fake_cursor`."""
    connection_pool = MagicMock(spec=PostgresConnectionPool)
    connection_pool.cursor.return_value.__enter__.return_value = fake_cursor
    connection_pool.cursor.return_value.__exit__.return_value = False
    return connection_pool
