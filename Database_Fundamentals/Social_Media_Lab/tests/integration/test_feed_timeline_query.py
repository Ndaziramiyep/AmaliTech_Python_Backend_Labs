"""Integration tests for PostgresFeedRepository's timeline query against a real Postgres database."""
from social.repositories.feed_repository import PostgresFeedRepository


def _create_user(cursor, username):
    """Insert a user with the given username and return its id."""
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, 'x') RETURNING id",
        (username, f"{username}@example.com"),
    )
    return cursor.fetchone()[0]


def _create_post(cursor, author_id, body):
    """Insert a post by the given author and return its id."""
    cursor.execute(
        "INSERT INTO posts (author_id, body) VALUES (%s, %s) RETURNING id",
        (author_id, body),
    )
    return cursor.fetchone()[0]


def test_get_timeline_returns_only_followed_authors_newest_first(cursor):
    """Test that the timeline includes only followed authors' posts, newest first."""
    alice = _create_user(cursor, "alice")
    bob = _create_user(cursor, "bob")
    carol = _create_user(cursor, "carol")
    cursor.execute(
        "INSERT INTO followers (follower_id, followee_id) VALUES (%s, %s)", (alice, bob)
    )
    _create_post(cursor, bob, "bob post 1")
    _create_post(cursor, bob, "bob post 2")
    _create_post(cursor, carol, "carol post - not followed")

    repository = PostgresFeedRepository()
    timeline = repository.get_timeline(cursor, follower_id=alice, limit=20)

    assert [p.body for p in timeline] == ["bob post 2", "bob post 1"]


def test_get_timeline_respects_limit(cursor):
    """Test that the timeline query returns no more posts than the given limit."""
    alice = _create_user(cursor, "alice")
    bob = _create_user(cursor, "bob")
    cursor.execute(
        "INSERT INTO followers (follower_id, followee_id) VALUES (%s, %s)", (alice, bob)
    )
    for i in range(5):
        _create_post(cursor, bob, f"post {i}")

    repository = PostgresFeedRepository()
    timeline = repository.get_timeline(cursor, follower_id=alice, limit=2)

    assert len(timeline) == 2
