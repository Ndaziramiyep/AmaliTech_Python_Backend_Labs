-- Bulk demo data for EXPLAIN ANALYZE: 5,000 more users, ~30 follows/user
-- (~150k rows), 50 posts/user (250k rows), plus a few likes/comments per
-- post so likes.count_by_posts / comments.count_by_posts have something
-- to aggregate. 10x the scale of the README's "Indexing & query
-- performance" writeup (500 users), for a more dramatic index vs.
-- seq-scan contrast. scripts/seed_data.py stays small on purpose (4 demo
-- users via the real App/service path); this script is for volume, so it
-- writes straight to the tables instead.
--
-- Safe to run against a database that already has rows in it (e.g. from
-- scripts/seed_data.py or tests) — random follower/followee/liker/
-- commenter ids are drawn from the users table's actual id set via
-- id_pool below, not assumed to be a fixed 1..N range, so pre-existing
-- rows and any id gaps don't break the foreign keys.
--
-- Run via pgAdmin's Query Tool, or `psql -f queries/bulk_seed.sql`. Not
-- idempotent — users/posts/comments have no uniqueness guard, so
-- re-running duplicates them. To start over completely:
--   TRUNCATE users RESTART IDENTITY CASCADE;

INSERT INTO users (username, email, password_hash, full_name, bio)
SELECT
    'user_' || i,
    'user_' || i || '@example.com',
    'not_a_real_hash',
    'Demo User ' || i,
    'Seeded for load testing.'
FROM generate_series(1, 5000) AS i;

-- Snapshot of every user id now in the table, as one array, so picking a
-- random existing id below is an O(1) index into id_pool rather than a
-- query that could reference a nonexistent id.
CREATE TEMP TABLE id_pool AS
SELECT array_agg(id) AS ids, count(*) AS n FROM users;

-- ~30 follow edges per user. chk_followers_no_self_follow and the
-- (follower_id, followee_id) primary key mean self-follows and
-- duplicates both need to be filtered/deduped before insert.
--
-- The random pick MUST be a plain SELECT-list expression against a
-- CROSS JOINed id_pool, not `(SELECT ... FROM id_pool)` as a subquery:
-- since id_pool doesn't reference anything from `u`, Postgres treats an
-- uncorrelated *subquery* here as a single constant to compute once (an
-- InitPlan, or a materialized/cached join side) and reuses it for every
-- row — even though random() is volatile — so every row would silently
-- get the same followee_id. A bare expression in the SELECT list has no
-- such hoisting: it's evaluated fresh per output row.
INSERT INTO followers (follower_id, followee_id)
SELECT DISTINCT follower_id, followee_id
FROM (
    SELECT
        u.id AS follower_id,
        ids[1 + floor(random() * n)] AS followee_id
    FROM users u
    CROSS JOIN generate_series(1, 30)
    CROSS JOIN id_pool
) candidates
WHERE follower_id <> followee_id
ON CONFLICT DO NOTHING;

-- 50 posts per user, created_at spread over the last 90 days so
-- ORDER BY created_at DESC actually has a range to sort through.
INSERT INTO posts (author_id, body, created_at)
SELECT
    u.id,
    'Post #' || gs || ' from user_' || u.id,
    now() - (random() * interval '90 days')
FROM users u
CROSS JOIN generate_series(1, 50) AS gs;

-- Up to 3 likes per post, excluding self-likes and deduped via the
-- (user_id, post_id) primary key. Same plain-expression-not-subquery
-- requirement as followers above, for the same reason.
INSERT INTO likes (user_id, post_id)
SELECT DISTINCT c.user_id, c.post_id
FROM (
    SELECT
        ids[1 + floor(random() * n)] AS user_id,
        p.id AS post_id,
        p.author_id
    FROM posts p
    CROSS JOIN generate_series(1, 3)
    CROSS JOIN id_pool
) c
WHERE c.user_id <> c.author_id
ON CONFLICT DO NOTHING;

-- 2 comments per post. Same requirement as above.
INSERT INTO comments (post_id, author_id, body)
SELECT
    p.id,
    ids[1 + floor(random() * n)],
    'Comment on post ' || p.id
FROM posts p
CROSS JOIN generate_series(1, 2)
CROSS JOIN id_pool;

DROP TABLE id_pool;

-- Refresh planner statistics so EXPLAIN ANALYZE reflects the new row
-- counts/distribution rather than stale (near-empty-table) estimates.
ANALYZE users;
ANALYZE followers;
ANALYZE posts;
ANALYZE likes;
ANALYZE comments;
