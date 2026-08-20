from social.repositories.feed_repository import PostgresFeedRepository


def _create_user(cursor, username):
    cursor.execute(
        "INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id",
        (username, f"{username}@example.com"),
    )
    return cursor.fetchone()[0]


def _create_post(cursor, author_id, body):
    cursor.execute(
        "INSERT INTO posts (author_id, body) VALUES (%s, %s) RETURNING id",
        (author_id, body),
    )
    return cursor.fetchone()[0]


def test_get_timeline_returns_only_followed_authors_newest_first(cursor):
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
