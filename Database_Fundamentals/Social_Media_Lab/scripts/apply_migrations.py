"""Apply every migrations/*.sql not yet recorded, in filename order.

Each migration runs in its own transaction. A schema_migrations table
tracks which filenames have already been applied so this is safe to re-run.
"""
import pathlib
import sys

import psycopg2

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from social.config import load_settings

MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parent.parent / "migrations"


def main() -> None:
    settings = load_settings()
    connection = psycopg2.connect(settings.postgres_dsn)
    try:
        with connection, connection.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(filename TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
            cursor.execute("SELECT filename FROM schema_migrations")
            applied = {row[0] for row in cursor.fetchall()}

        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                print(f"skip  {path.name} (already applied)")
                continue
            with connection, connection.cursor() as cursor:
                cursor.execute(path.read_text())
                cursor.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,)
                )
            print(f"apply {path.name}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
