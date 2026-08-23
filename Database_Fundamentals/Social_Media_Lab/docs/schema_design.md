# Schema Design

## Tables

| Table       | Primary key                 | Foreign keys                                   |
|-------------|------------------------------|-------------------------------------------------|
| users       | id                            | —                                                |
| posts       | id                            | author_id → users.id                            |
| comments    | id                            | post_id → posts.id, author_id → users.id        |
| followers   | (follower_id, followee_id)    | follower_id → users.id, followee_id → users.id  |
| likes       | (user_id, post_id)            | user_id → users.id, post_id → posts.id          |

All foreign keys are `ON DELETE CASCADE`: deleting a user or post removes the
rows that depend on it (their comments, likes, follow edges, posts) rather
than leaving orphans.

## 3NF justification

A relation is in 3NF when every non-key attribute depends on the whole key,
nothing but the key (no partial dependency on part of a composite key), and
no non-key attribute depends on another non-key attribute (no transitive
dependency).

- **users** — `username`, `email`, `password_hash`, `created_at`,
  `full_name`, `bio`, and `is_active` each describe the user identified by
  `id` directly, and no non-key attribute determines another (`full_name`
  and `bio` don't determine `is_active`, or vice versa — they're
  independent, single-valued facts about the same user). No repeating
  groups. 3NF.

- **posts** — `author_id`, `body`, `metadata`, `created_at` all depend only
  on `id`, the post's surrogate key. `metadata` (JSONB) holds free-form,
  variable-shape attributes (tags, location) that describe *this post* and
  nothing else — they don't determine or get determined by `body` or
  `author_id`, so storing them as one JSONB value doesn't reintroduce a
  transitive or multi-valued dependency; it is a deliberate, documented
  denormalization for schema flexibility, not a normalization violation.
  If `tags` needed to be queried/joined relationally (e.g. "all posts with
  tag X" at scale) it would be extracted into its own `tags` /
  `post_tags` tables — but that's a query-shape decision, not a 3NF one.

- **comments** — `body` and `created_at` depend only on `id`; `post_id` and
  `author_id` are foreign keys, not derived attributes. No column depends on
  another column that isn't the key. 3NF.

- **followers** — a pure associative (many-to-many) table with no non-key
  attributes besides `created_at`, which depends on the whole composite key
  `(follower_id, followee_id)` — the moment *that specific edge* was
  created — not on either column alone. No partial dependency. The
  `chk_followers_no_self_follow` CHECK constraint enforces the business rule
  that a user cannot follow themselves. 3NF.

- **likes** — same shape as `followers`: `created_at` depends on the full
  composite key `(user_id, post_id)`, not on either column individually.
  3NF.

No table stores a value derivable from other columns (e.g. no cached
`like_count` on `posts`) and no column takes on multiple independent
meanings, so all five tables satisfy 1NF, 2NF, and 3NF.

## Indexing

- `idx_posts_author_id`, `idx_comments_post_id`, `idx_comments_author_id` —
  support the FK lookups implied by cascading deletes and basic joins.
- `followers_pkey` (composite B-tree on `follower_id, followee_id`,
  defined in `src/social/database/schema.py`) — doubles as the uniqueness
  constraint on a follow edge and as the access path the feed timeline
  query uses: given a `follower_id`, find every `followee_id`.
- `idx_posts_author_created_at` (`author_id, created_at DESC`) — lets the
  feed timeline query fetch each followed author's posts pre-sorted,
  avoiding a full sort after the join. Measured with `EXPLAIN ANALYZE` in
  Phase 5 below.
- `idx_likes_post_id` — supports the trending-posts aggregation, which
  groups likes by `post_id` over a recent time window.

### EXPLAIN ANALYZE: feed timeline query

Seeded 500 users, ~30 follow edges/user (15,000 rows), 50 posts/user (25,000
rows), then ran `EXPLAIN (ANALYZE, BUFFERS)` on `queries/feed_timeline.sql`
for one follower (30 followees, ~1,500 candidate posts, `LIMIT 20`) before
and after adding `followers_pkey`/`idx_posts_author_created_at` to the schema.

**Before** (no `followers_pkey`, no `idx_posts_author_created_at`):

```text
Limit  (actual time=5.993..5.999 rows=20 loops=1)
  ->  Sort  (actual time=5.992..5.995 rows=20 loops=1)              -- top-N heapsort
        Sort Key: p.created_at DESC, p.id DESC
        ->  Hash Join  (actual time=1.088..5.356 rows=1500 loops=1)
              ->  Seq Scan on posts p  (rows=25000 loops=1)          -- full table
              ->  Hash
                    ->  Seq Scan on followers f  (rows=30 loops=1)
                          Filter: (follower_id = 1)
                          Rows Removed by Filter: 14970               -- scanned all 15,000
Execution Time: 6.034 ms
```

**After**:

```text
Limit  (actual time=3.533..3.537 rows=20 loops=1)
  ->  Sort  (actual time=3.531..3.534 rows=20 loops=1)
        Sort Key: p.created_at DESC, p.id DESC
        ->  Hash Join  (actual time=0.195..3.119 rows=1500 loops=1)
              ->  Seq Scan on posts p  (rows=25000 loops=1)
              ->  Hash
                    ->  Bitmap Heap Scan on followers f  (rows=30 loops=1)
                          Recheck Cond: (follower_id = 1)
                          ->  Bitmap Index Scan on followers_pkey
                                Index Cond: (follower_id = 1)          -- 30 rows, not 15,000
Execution Time: 3.571 ms
```

`followers_pkey` turned "scan all 15,000 follow edges, throw away 14,970" into
a direct index lookup for this follower's ~30 followees — the dominant win
(6.03ms → 3.57ms, ~40% less time, and the followers side reads shared
buffers 96 → 30+2 instead of scanning the whole table).

`idx_posts_author_created_at`, however, is **not** used here: the planner
still Seq Scans all 25,000 posts in both plans. At this selectivity (30 of
500 authors, ~1,500 of 25,000 posts) and with the query fetching only
`LIMIT 20` after sorting the *entire* matched set, one sequential scan +
hash join + top-N heapsort over the small candidate set is cheaper than 30
separate per-author index probes. The composite index would earn its keep
at higher post-table scale (fewer authors to fan out over, or a much larger
`posts` table making the seq scan itself expensive), or on the single-author
query it was also built for — `SELECT ... FROM posts WHERE author_id = %s
ORDER BY created_at DESC` — which it serves directly via index-only ordering
with no sort step at all, regardless of table size. This is the expected,
correct planner choice, not an unused index: `EXPLAIN` on data at the scale
this app actually runs at should be re-checked before assuming either index
"isn't helping."
