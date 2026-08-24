"""Constraints that only a real Postgres enforces - no fake can verify these."""
import psycopg2
import pytest


def test_all_five_tables_exist(cursor):
    """Test that the users, posts, comments, followers, and likes tables all exist."""
    cursor.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    )
    tables = {row[0] for row in cursor.fetchall()}

    assert {"users", "posts", "comments", "followers", "likes"} <= tables


def test_followers_self_follow_is_rejected(cursor):
    """Test that inserting a followers row where a user follows themselves violates a check constraint."""
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES ('ada', 'ada@example.com', 'x') RETURNING id"
    )
    (user_id,) = cursor.fetchone()

    with pytest.raises(psycopg2.errors.CheckViolation):
        cursor.execute(
            "INSERT INTO followers (follower_id, followee_id) VALUES (%s, %s)",
            (user_id, user_id),
        )
