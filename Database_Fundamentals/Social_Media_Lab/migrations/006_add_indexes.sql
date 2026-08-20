-- Composite B-tree index on followers(follower_id, followee_id), enforced
-- as the table's primary key so every INSERT also protects against
-- duplicate follow edges. Column order matches the feed timeline's access
-- pattern: "given a follower_id, find all followee_id values."
ALTER TABLE followers
    ADD CONSTRAINT followers_pkey PRIMARY KEY (follower_id, followee_id);

-- Supports feed_timeline.sql: per-author posts ordered newest-first.
CREATE INDEX idx_posts_author_created_at ON posts (author_id, created_at DESC);

-- Supports trending_posts.sql: counting likes per post over a time window.
CREATE INDEX idx_likes_post_id ON likes (post_id);
