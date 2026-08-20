-- Likes: a user liking a post, at most once each.
CREATE TABLE likes (
    user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    post_id BIGINT NOT NULL REFERENCES posts (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, post_id)
);
