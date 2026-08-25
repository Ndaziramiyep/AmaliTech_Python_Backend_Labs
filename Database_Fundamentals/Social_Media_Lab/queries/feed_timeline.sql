-- Given a follower_id, fetch the newest posts from everyone they follow.
-- dialect: postgresql
-- Access pattern the followers_pkey composite index and
-- idx_posts_author_created_at (both in src/social/database/schema.py)
-- exist for. See README.md "Indexing & query performance" for the
-- EXPLAIN ANALYZE before/after this index was added.
--
-- $1 = follower_id, $2 = limit. These are standard SQL positional
-- parameters (valid on their own, unlike psycopg2's %s style), so this
-- file runs as-is via `psql -f queries/feed_timeline.sql` with `PREPARE`/
-- `EXECUTE`, or `\bind`. The repository (src/social/repositories/
-- feed_repository.py) runs the %s form of the same query through psycopg2.
SELECT p.id, p.author_id, p.body, p.metadata, p.created_at
FROM posts p
JOIN followers f ON f.followee_id = p.author_id
WHERE f.follower_id = $1
ORDER BY p.created_at DESC, p.id DESC
LIMIT $2;
