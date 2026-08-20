-- Followers: a directed edge in the social graph. The composite primary
-- key (and its backing B-tree index) is added in 006_add_indexes.sql, once
-- all tables it could reference exist.
CREATE TABLE followers (
    follower_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    followee_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_followers_no_self_follow CHECK (follower_id <> followee_id)
);
