"""Integration fixtures against a real Postgres, per docker-compose.yml.

Skips the whole integration suite if Postgres isn't reachable, rather than
failing - these tests document real infrastructure behavior, they don't
replace the fakes-based unit tests.
"""
import pytest
import psycopg2

from social.config import load_settings

MIGRATIONS = [
    "001_create_users.sql",
    "002_create_posts.sql",
    "003_create_comments.sql",
    "004_create_followers.sql",
    "005_create_likes.sql",
    "006_add_indexes.sql",
]


@pytest.fixture(scope="session")
def postgres_dsn():
    settings = load_settings()
    try:
        connection = psycopg2.connect(settings.postgres_dsn, connect_timeout=2)
        connection.close()
    except psycopg2.OperationalError as exc:
        pytest.skip(f"Postgres not reachable at {settings.postgres_dsn}: {exc}")
    return settings.postgres_dsn


@pytest.fixture
def cursor(postgres_dsn):
    import pathlib

    connection = psycopg2.connect(postgres_dsn)
    try:
        with connection.cursor() as setup_cursor:
            setup_cursor.execute(
                "DROP TABLE IF EXISTS likes, comments, followers, posts, users CASCADE"
            )
        connection.commit()

        migrations_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "migrations"
        for filename in MIGRATIONS:
            with connection.cursor() as setup_cursor:
                setup_cursor.execute((migrations_dir / filename).read_text())
            connection.commit()

        with connection.cursor() as test_cursor:
            yield test_cursor
        connection.rollback()
    finally:
        connection.close()
