"""Data access for the users table. No business logic, no commits."""
from typing import Any, Optional, Sequence

from social.domain.models import User


_COLUMNS = "id, username, email, password_hash, created_at"


class PostgresUserRepository:
    def create(self, cursor: Any, user: User) -> User:
        cursor.execute(
            f"""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING {_COLUMNS}
            """,
            (user.username, user.email, user.password_hash),
        )
        return _row_to_user(cursor.fetchone())

    def get_by_id(self, cursor: Any, user_id: int) -> Optional[User]:
        cursor.execute(
            f"SELECT {_COLUMNS} FROM users WHERE id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        return _row_to_user(row) if row else None

    def get_by_username(self, cursor: Any, username: str) -> Optional[User]:
        cursor.execute(
            f"SELECT {_COLUMNS} FROM users WHERE username = %s",
            (username,),
        )
        row = cursor.fetchone()
        return _row_to_user(row) if row else None

    def get_by_email(self, cursor: Any, email: str) -> Optional[User]:
        cursor.execute(
            f"SELECT {_COLUMNS} FROM users WHERE email = %s",
            (email,),
        )
        row = cursor.fetchone()
        return _row_to_user(row) if row else None

    def list_all(self, cursor: Any) -> Sequence[User]:
        cursor.execute(f"SELECT {_COLUMNS} FROM users ORDER BY id")
        return [_row_to_user(row) for row in cursor.fetchall()]


def _row_to_user(row: Any) -> User:
    user_id, username, email, password_hash, created_at = row
    return User(
        id=user_id,
        username=username,
        email=email,
        password_hash=password_hash,
        created_at=created_at,
    )
