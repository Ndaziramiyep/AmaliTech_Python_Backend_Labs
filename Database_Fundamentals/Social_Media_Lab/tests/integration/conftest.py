"""Integration fixtures against a real Postgres, per the POSTGRES_* vars in .env.

Runs against a separate <dbname>_test database, created on demand - never
the same database load_settings() points the CLI/REPL at. The `cursor`
fixture below unconditionally drops and rebuilds all 5 tables on every test;
pointed at the app's real database, that would wipe out anything created
through the CLI the moment the suite ran.

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
    "007_add_password_to_users.sql",
]


def _test_dsn(app_dsn: str) -> str:
    root, _, dbname = app_dsn.rpartition("/")
    return f"{root}/{dbname}_test"


def _ensure_database_exists(dsn: str) -> None:
    root, _, dbname = dsn.rpartition("/")
    connection = psycopg2.connect(f"{root}/postgres", connect_timeout=2)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            if cursor.fetchone() is None:
                cursor.execute(f'CREATE DATABASE "{dbname}"')
    finally:
        connection.close()


@pytest.fixture(scope="session")
def postgres_dsn():
    settings = load_settings()
    test_dsn = _test_dsn(settings.postgres_dsn)
    try:
        _ensure_database_exists(test_dsn)
        connection = psycopg2.connect(test_dsn, connect_timeout=2)
        connection.close()
    except psycopg2.OperationalError as exc:
        pytest.skip(f"Postgres not reachable at {test_dsn}: {exc}")
    return test_dsn


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
