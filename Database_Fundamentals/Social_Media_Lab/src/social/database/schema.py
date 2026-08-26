"""Creates the app's entire schema on demand using idempotent `IF NOT EXISTS` statements, so running it against an already-initialized database is a fast no-op rather than an error."""
from typing import Any

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    full_name VARCHAR(150) NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Posts: authored content. metadata holds variable, non-relational
-- attributes (tags, location) that don't participate in functional
-- dependencies with the rest of the row, so a single JSONB column doesn't
-- violate 3NF (see README.md, "Normalization (3NF)").
CREATE TABLE IF NOT EXISTS posts (
    id BIGSERIAL PRIMARY KEY,
    author_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_posts_author_id ON posts (author_id);
CREATE INDEX IF NOT EXISTS idx_posts_author_created_at ON posts (author_id, created_at DESC);
-- Supports PostgresPostRepository.list_recent's global
-- ORDER BY created_at DESC, id DESC, LIMIT %s: without this, that query
-- has no per-author filter to narrow on, so it seq-scans and sorts the
-- whole table every call.
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts (created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS comments (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts (id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments (post_id);
CREATE INDEX IF NOT EXISTS idx_comments_author_id ON comments (author_id);
-- Supports PostgresCommentRepository.list_by_post's
-- WHERE post_id = %s ORDER BY created_at ASC: idx_comments_post_id alone
-- finds the right rows but still needs a separate sort step, since it
-- isn't ordered by created_at.
CREATE INDEX IF NOT EXISTS idx_comments_post_created_at ON comments (post_id, created_at);

-- Composite primary key doubles as the uniqueness constraint on a follow
-- edge and as the feed timeline's access path: given a follower_id, find
-- every followee_id.
CREATE TABLE IF NOT EXISTS followers (
    follower_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    followee_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (follower_id, followee_id),
    CONSTRAINT chk_followers_no_self_follow CHECK (follower_id <> followee_id)
);
-- The (follower_id, followee_id) primary key above already supports
-- list_following (WHERE follower_id = %s), since follower_id leads it.
-- It does nothing for the reverse direction: list_followers
-- (WHERE followee_id = %s ORDER BY created_at DESC) had no supporting
-- index at all and fell back to a full sequential scan.
CREATE INDEX IF NOT EXISTS idx_followers_followee_id ON followers (followee_id, created_at DESC);

CREATE TABLE IF NOT EXISTS likes (
    user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    post_id BIGINT NOT NULL REFERENCES posts (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, post_id)
);
CREATE INDEX IF NOT EXISTS idx_likes_post_id ON likes (post_id);
"""


def ensure_schema(connection: Any) -> None:
    """Create every table/index this app needs against `connection`, if they don't already exist."""
    with connection, connection.cursor() as cursor:
        cursor.execute(_SCHEMA_SQL)
