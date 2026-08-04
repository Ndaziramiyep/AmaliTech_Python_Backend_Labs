"""Integration tests for PostgresConnectionPool's exhaustion and rollback behavior."""

from __future__ import annotations

import pytest

from social_platform.config.application_settings import ApplicationSettings, PostgresSettings
from social_platform.database.postgres_connection_pool import PostgresConnectionPool
from social_platform.models.exceptions import ConnectionPoolExhaustedError

pytestmark = pytest.mark.integration


def test_a_second_checkout_from_an_exhausted_pool_raises_a_domain_error() -> None:
    """A pool sized to one connection reports exhaustion as a domain error, not psycopg2's."""
    base_settings = ApplicationSettings.from_environment().postgres
    single_connection_settings = PostgresSettings(
        host=base_settings.host,
        port=base_settings.port,
        database_name=base_settings.database_name,
        username=base_settings.username,
        password=base_settings.password,
        pool_min_size=1,
        pool_max_size=1,
    )
    pool = PostgresConnectionPool(single_connection_settings)

    with pool.cursor():
        with pytest.raises(ConnectionPoolExhaustedError):
            with pool.cursor():
                pass

    pool.close_all_connections()


def test_a_failed_transaction_is_rolled_back_and_does_not_persist() -> None:
    """An exception inside the cursor context manager rolls back, leaving no partial row."""
    settings = ApplicationSettings.from_environment().postgres
    pool = PostgresConnectionPool(settings)
    with pool.cursor() as cursor:
        cursor.execute("TRUNCATE users RESTART IDENTITY CASCADE")

    with pytest.raises(RuntimeError):
        with pool.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, display_name) "
                "VALUES ('ada', 'ada@example.com', 'hash', 'Ada Lovelace')"
            )
            raise RuntimeError("simulated failure after the insert")

    with pool.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS row_count FROM users")
        row = cursor.fetchone()
        assert row is not None
        assert row["row_count"] == 0

    pool.close_all_connections()
