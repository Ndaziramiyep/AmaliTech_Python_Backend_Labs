"""Data access for the users table. No business logic, no commits."""
from typing import Any, Optional, Sequence

import psycopg2

from social.exceptions import DuplicateEmailError, DuplicateUsernameError
from social.models import User


_COLUMNS = "id, username, email, password_hash, created_at, full_name, bio, is_active"


class PostgresUserRepository:
    def create(self, cursor: Any, user: User) -> User:
        try:
            cursor.execute(
                f"""
                INSERT INTO users (username, email, password_hash, full_name, bio)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING {_COLUMNS}
                """,
                (user.username, user.email, user.password_hash, user.full_name, user.bio),
            )
        except psycopg2.errors.UniqueViolation as exc:
            constraint = exc.diag.constraint_name
            if constraint == "users_username_key":
                raise DuplicateUsernameError(
                    f"Username {user.username!r} is already taken."
                ) from exc
            if constraint == "users_email_key":
                raise DuplicateEmailError(
                    f"Email {user.email!r} is already registered."
                ) from exc
            raise
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

    def update_profile(
        self, cursor: Any, user_id: int, full_name: str, bio: str
    ) -> Optional[User]:
        cursor.execute(
            f"""
            UPDATE users SET full_name = %s, bio = %s
            WHERE id = %s
            RETURNING {_COLUMNS}
            """,
            (full_name, bio, user_id),
        )
        row = cursor.fetchone()
        return _row_to_user(row) if row else None


def _row_to_user(row: Any) -> User:
    user_id, username, email, password_hash, created_at, full_name, bio, is_active = row
    return User(
        id=user_id,
        username=username,
        email=email,
        password_hash=password_hash,
        created_at=created_at,
        full_name=full_name,
        bio=bio,
        is_active=is_active,
    )
