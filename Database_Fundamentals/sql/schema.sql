-- Normalized (3NF) schema for the social media platform data backend.

CREATE TABLE IF NOT EXISTS users (
    user_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username       VARCHAR(50)  NOT NULL UNIQUE,
    email          VARCHAR(255) NOT NULL UNIQUE,
    password_hash  TEXT         NOT NULL,
    display_name   VARCHAR(100) NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
);

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

CREATE TABLE IF NOT EXISTS comments (
    comment_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    post_id             BIGINT       NOT NULL REFERENCES posts (post_id) ON DELETE CASCADE,
    commenter_user_id   BIGINT       NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    content             TEXT         NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments (post_id);

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
