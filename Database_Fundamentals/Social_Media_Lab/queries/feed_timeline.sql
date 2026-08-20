-- Given a follower_id, fetch the newest posts from everyone they follow.
-- Access pattern the followers_pkey composite index and
-- idx_posts_author_created_at (both migrations/006_add_indexes.sql) exist
-- for. See docs/schema_design.md "Indexing" for the EXPLAIN ANALYZE before/
-- after this index was added.
SELECT p.id, p.author_id, p.body, p.metadata, p.created_at
FROM posts p
JOIN followers f ON f.followee_id = p.author_id
WHERE f.follower_id = %s
ORDER BY p.created_at DESC, p.id DESC
LIMIT %s;
