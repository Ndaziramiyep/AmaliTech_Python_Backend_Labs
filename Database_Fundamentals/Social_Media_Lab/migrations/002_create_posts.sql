-- Posts: authored content. metadata holds variable, non-relational attributes
-- (tags, location) that do not participate in functional dependencies with
-- the rest of the row, so keeping them as a single JSONB value does not
-- violate 3NF (see docs/schema_design.md).
CREATE TABLE posts (
    id BIGSERIAL PRIMARY KEY,
    author_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_posts_author_id ON posts (author_id);
