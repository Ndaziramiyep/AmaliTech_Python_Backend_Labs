-- Normalized (3NF) schema for the social media platform data backend.
-- dialect: postgresql

CREATE TABLE IF NOT EXISTS users (
    user_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username       VARCHAR(50)  NOT NULL UNIQUE,
    email          VARCHAR(255) NOT NULL UNIQUE,
    password_hash  TEXT         NOT NULL,
    bio            VARCHAR(280),
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- `metadata` now only ever holds `{"location": "..."}` -- tags moved to a proper
-- many-to-many relationship (`tags` + `post_tags` below) instead of a JSONB array,
-- since "which posts have this tag" and "how many posts use this tag" are exactly the
-- kind of question a JSONB array can't index or join on efficiently.
CREATE TABLE IF NOT EXISTS posts (
    post_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_user_id   BIGINT       NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    content          TEXT         NOT NULL,
    metadata         JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Serves the feed query's join-then-sort (posts by a given author, newest first) and
-- is the composite index that turns the feed's window-function scan into an index scan.
CREATE INDEX IF NOT EXISTS idx_posts_author_created_at
    ON posts (author_user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS tags (
    tag_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name     VARCHAR(50) NOT NULL UNIQUE
);

-- The many-to-many join table between posts and tags: one post can carry several
-- tags, and one tag can be attached to many posts. The composite primary key
-- prevents attaching the same tag to the same post twice and doubles as the
-- "which tags does this post have" index.
CREATE TABLE IF NOT EXISTS post_tags (
    post_id   BIGINT NOT NULL REFERENCES posts (post_id) ON DELETE CASCADE,
    tag_id    BIGINT NOT NULL REFERENCES tags (tag_id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

-- Serves the reverse "which posts use this tag" direction without scanning the
-- whole join table.
CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags (tag_id);

-- `parent_comment_id` makes a comment either top-level (NULL) or a reply to another
-- comment on the same post (self-referencing adjacency list), so a comment thread of
-- arbitrary depth is an ordinary recursive query instead of a fixed number of columns.
CREATE TABLE IF NOT EXISTS comments (
    comment_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    post_id             BIGINT       NOT NULL REFERENCES posts (post_id) ON DELETE CASCADE,
    commenter_user_id   BIGINT       NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    parent_comment_id   BIGINT       REFERENCES comments (comment_id) ON DELETE CASCADE,
    content             TEXT         NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments (post_id);

-- Serves "which comments reply to this comment" -- the recursive step of the
-- comment-thread query walks this direction one level at a time.
CREATE INDEX IF NOT EXISTS idx_comments_parent_comment_id ON comments (parent_comment_id);

CREATE TABLE IF NOT EXISTS followers (
    follower_user_id   BIGINT      NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    followee_user_id   BIGINT      NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (follower_user_id, followee_user_id),
    CHECK (follower_user_id <> followee_user_id)
);

-- The primary key's leading column (follower_user_id) already serves "who does this
-- user follow" lookups for free. This second composite index serves the reverse
-- "who follows this user" lookups without scanning the whole table.
CREATE INDEX IF NOT EXISTS idx_followers_followee_follower
    ON followers (followee_user_id, follower_user_id);

-- Likes are a real relational fact, not just an activity-log entry: the composite
-- primary key makes "like the same post twice" a no-op (INSERT ... ON CONFLICT DO
-- NOTHING) instead of a duplicate row or a raised error, the same idempotency
-- pattern used by `followers`. MongoDB's activity log still records that the like
-- *event* happened, but this table is the source of truth for *whether* it's liked.
CREATE TABLE IF NOT EXISTS likes (
    post_id      BIGINT      NOT NULL REFERENCES posts (post_id) ON DELETE CASCADE,
    user_id      BIGINT      NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (post_id, user_id)
);

-- Serves "which posts has this user liked" without scanning the whole table; the
-- primary key's leading column already serves "who liked this post" for free.
CREATE INDEX IF NOT EXISTS idx_likes_user_id ON likes (user_id);
