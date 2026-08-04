# Social Media Platform Data Backend

A data backend for a social media platform: a normalized PostgreSQL schema for users, posts,
comments, and followers; a transactional follow/unfollow feature built on psycopg2 connection
pooling; Redis-cached timelines; and MongoDB-backed activity logging. The main engineering focus
is the timeline feed query — a CTE + JOIN + `ROW_NUMBER()` query backed by composite B-tree
indexes and verified with `EXPLAIN ANALYZE`.

## Contents

- [Setup](#setup)
- [Usage](#usage)
- [Project layout](#project-layout)
- [Architecture](#architecture)
- [The transactional follow/unfollow contract](#the-transactional-followunfollow-contract)
- [Feed query performance](#feed-query-performance)
- [Error handling](#error-handling)
- [Scope decisions](#scope-decisions)
- [Testing, formatting, and type-checking](#testing-formatting-and-type-checking)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
pip install -e .

copy .env.example .env        # cp .env.example .env on macOS/Linux
docker-compose up -d          # PostgreSQL, Redis, MongoDB
```

`docker-compose up -d` applies [`sql/schema.sql`](sql/schema.sql) automatically on first boot via
Postgres's `docker-entrypoint-initdb.d` mechanism. To apply it to an existing database by hand:

```bash
psql -h localhost -U social_platform -d social_platform -f sql/schema.sql
```

## Usage

Every operation is backed by a thin composition-root module in
[`src/social_platform/cli/`](src/social_platform/cli/); each reads connection settings from the
environment via [`ApplicationSettings`](src/social_platform/config/application_settings.py). You
can reach them two ways: through [`main.py`](main.py), a single dispatcher over every command, or
through the equivalent standalone script under [`scripts/`](scripts/) — both call the same
composition-root `main()` function, so behavior is identical either way.

```bash
# via the unified entry point
python main.py register-user <username> <email> <password> "<display name>"
python main.py create-post <author_user_id> "post content" --tag python --tag postgres --location Kigali
python main.py follow-user <follower_user_id> <followee_user_id>
python main.py unfollow-user <follower_user_id> <followee_user_id>
python main.py add-comment <post_id> <commenter_user_id> "nice post"
python main.py like-post <actor_user_id> <post_id>
python main.py get-user-feed <follower_user_id> --page 1
python main.py get-trending-posts --since-hours 24 --limit 10

# equivalently, via the standalone scripts
python scripts/register_user.py <username> <email> <password> "<display name>"
python scripts/follow_user.py <follower_user_id> <followee_user_id>
python scripts/analyze_feed_query.py   # diagnostic only; no main.py subcommand
```

`follow-user` and `unfollow-user` are idempotent: running either twice in a row is a no-op
success (`Follow result: already_exists`, `Unfollow result: did_not_exist`), never an error.

## Project layout

```text
Database_Fundamentals/
├── docker-compose.yml           # PostgreSQL, Redis, MongoDB for local development
├── sql/schema.sql                # 3NF DDL: tables, constraints, indexes
├── docs/er_diagram.md            # Mermaid ER diagram
├── scripts/                      # thin CLI entry points
├── src/social_platform/
│   ├── config/                   # environment-driven settings, no deps on other layers
│   ├── models/                   # entities, result enums, exceptions — no deps on other layers
│   ├── database/                 # connection pooling/factories — depends on config
│   ├── repositories/             # interfaces (DIP/ISP) + Postgres/Redis/Mongo implementations
│   ├── services/                 # business logic — depends only on repository interfaces
│   └── cli/                      # composition root — wires concrete repositories to services
└── tests/
    ├── unit/                     # mirrors src/, mocked psycopg2 + fakeredis/mongomock + fakes
    └── integration/               # real docker-compose services, `pytest -m integration`
```

## Architecture

Dependency direction is strictly inward: `cli` → `services` → `repositories/interfaces.py` ←
`repositories/postgres_*.py` / `redis_*.py` / `mongo_*.py` → `database` → `config` / `models`.

- **`models/`** — dataclass entities (`User`, `Post`, `Comment`, `FollowRelationship`,
  `FeedPostEntry`, `TrendingPostEntry`, `ActivityEvent`), the `FollowResult`/`UnfollowResult`
  outcome enums, and the domain exception hierarchy. No psycopg2/redis/pymongo import ever
  appears here.
- **`repositories/interfaces.py`** — one narrow abstract base class per aggregate
  (`UserRepositoryInterface`, `PostRepositoryInterface`, `CommentRepositoryInterface`,
  `FollowerRepositoryInterface`, `TimelineCacheRepositoryInterface`,
  `ActivityLogRepositoryInterface`) — Dependency Inversion and Interface Segregation in
  practice: services depend on these, never on `Postgres*`/`Redis*`/`Mongo*` classes directly.
- **`services/`** — one class per use case, each taking its repository dependencies through its
  constructor. No service ever imports psycopg2, redis, or pymongo.
- **`cli/`** — the only layer allowed to construct concrete repositories
  ([`cli/_composition.py`](src/social_platform/cli/_composition.py)) and translate domain
  exceptions into exit codes.

## The transactional follow/unfollow contract

`UserFollowingService.follow_user` / `unfollow_user`
([source](src/social_platform/services/user_following_service.py)) is the feature this lab
grades most heavily, so its contract is explicit rather than left to convention:

1. **Self-follow is rejected up front** (`InvalidFollowOperationError`) before any SQL runs —
   a clean domain error instead of a parsed `CheckViolation`.
2. **The follow/unfollow edge write is one atomic PostgreSQL transaction**
   ([`PostgresFollowerRepository`](src/social_platform/repositories/postgres_follower_repository.py)):
   `INSERT ... ON CONFLICT (follower_user_id, followee_user_id) DO NOTHING` for follow,
   a plain `DELETE` for unfollow. `PostgresConnectionPool.cursor()`
   ([source](src/social_platform/database/postgres_connection_pool.py)) commits on a clean exit
   and rolls back on any exception — the repository and service never touch a raw connection.
3. **Idempotent, not error-prone.** Re-following an already-followed user returns
   `FollowResult.ALREADY_EXISTS`; unfollowing a user not followed returns
   `UnfollowResult.DID_NOT_EXIST`. Neither raises.
4. **A nonexistent follower or followee** raises `UserNotFoundError` — the repository catches
   `psycopg2.errors.ForeignKeyViolation` and translates it; no raw psycopg2 exception type ever
   crosses the repository boundary.
5. **Pool exhaustion** raises `ConnectionPoolExhaustedError`, translated from
   `psycopg2.pool.PoolError` inside `PostgresConnectionPool.cursor()`.
6. **The MongoDB activity-log write happens only after the PostgreSQL transaction commits**, and
   is best-effort: a logging failure is caught and logged, never allowed to undo or fail an
   already-committed follow/unfollow. Cross-store two-phase commit is intentionally out of
   scope (see [Scope decisions](#scope-decisions)) — PostgreSQL is the single source of truth
   for the follow graph.

All five edge cases (self-follow, nonexistent user, duplicate follow, unfollow of a missing
edge, pool exhaustion) are covered against a **real** PostgreSQL instance in
[`tests/integration/test_transactional_follow.py`](tests/integration/test_transactional_follow.py)
and
[`tests/integration/test_postgres_connection_pool.py`](tests/integration/test_postgres_connection_pool.py) —
a mocked cursor would happily "succeed" on a self-follow insert that only a real `CHECK`
constraint rejects.

## Feed query performance

The timeline feed query
([`postgres_post_repository.py`](src/social_platform/repositories/postgres_post_repository.py))
uses two CTEs, a JOIN, and `ROW_NUMBER()` for pagination:

```sql
WITH followed_users AS (
    SELECT followee_user_id FROM followers WHERE follower_user_id = %(follower_user_id)s
),
timeline_posts AS (
    SELECT posts.*, ROW_NUMBER() OVER (ORDER BY posts.created_at DESC, posts.post_id DESC) AS row_number
    FROM posts JOIN followed_users ON followed_users.followee_user_id = posts.author_user_id
)
SELECT timeline_posts.*, users.username AS author_username
FROM timeline_posts JOIN users ON users.user_id = timeline_posts.author_user_id
WHERE timeline_posts.row_number BETWEEN %(first_row)s AND %(last_row)s
ORDER BY timeline_posts.row_number
```

Two indexes back it:

- `followers` primary key `(follower_user_id, followee_user_id)` — its leading column already
  serves the first CTE ("who does this user follow") without a dedicated index.
- `idx_followers_followee_follower (followee_user_id, follower_user_id)` — serves the reverse
  "who follows this user" direction.
- **`idx_posts_author_created_at (author_user_id, created_at DESC)`** — the index that actually
  accelerates the feed: it turns the join-then-sort into an index scan feeding `ROW_NUMBER()`,
  instead of a sequential scan over `posts` followed by an in-memory sort.

Run `python scripts/analyze_feed_query.py` to see `EXPLAIN ANALYZE` output for the feed query
with and without `idx_posts_author_created_at` (it drops the index, re-runs the plan, then
restores it). With the index present, the plan shows an index scan on
`idx_posts_author_created_at` feeding the window function directly; without it, the planner
falls back to a sequential scan on `posts` plus an explicit sort step — the difference the
composite index is there to eliminate.

## Error handling

| Exception | Raised when |
| --- | --- |
| `InvalidFollowOperationError` | A user attempts to follow or unfollow themselves. |
| `UserNotFoundError` | An operation references a user id that does not exist (foreign key violation). |
| `UserAlreadyExistsError` | Registration is attempted with a username or email already taken. |
| `PostNotFoundError` | An operation references a post id that does not exist. |
| `ConnectionPoolExhaustedError` | No PostgreSQL connection is available from the pool. |

Every CLI command catches `SocialPlatformError` (the root of this hierarchy), prints a clean
message to stderr, and exits with status 1 — no raw tracebacks or psycopg2 exception types ever
reach the terminal.

## Scope decisions

- **Trending posts uses PostgreSQL only** (posts ranked by recent comment count via a
  `GROUP BY` CTE), not a Postgres/MongoDB score merge. The lab's "complex queries" requirement
  is CTE+JOIN (feed) and `ROW_NUMBER()` (pagination) — both already demonstrated by the feed
  query — and MongoDB is already exercised independently by activity logging on every
  follow/post/comment/like action plus the Mongo-only `like_post` write path. A cross-store
  merge algorithm would add real risk for a lab graded on feed performance and transactional
  correctness, not trending.
- **Likes have no PostgreSQL table.** Per the lab's data-store split ("MongoDB: store activity
  logs (likes, follows, etc.)"), a like is recorded only as a MongoDB activity-log document via
  `PostEngagementService.like_post` — there is no relational `likes` table to keep in sync.
- **No cross-store two-phase commit.** The MongoDB activity-log write for follows/posts/comments
  is best-effort and happens after the PostgreSQL transaction commits (see
  [above](#the-transactional-followunfollow-contract)). PostgreSQL is the single source of
  truth; a lost activity-log write is logged but never rolls back an already-committed action.
- **The Redis timeline cache uses a fixed TTL, not write-time invalidation.** Creating a post
  does not proactively invalidate every follower's cached feed page (that "fan-out on write"
  approach breaks down for high-follower-count accounts). Instead, cached pages simply expire
  after `TIMELINE_CACHE_TTL_SECONDS` (default 60s) — a deliberate "fan-out on read, short TTL"
  trade-off favoring high-read-workload performance.

## Testing, formatting, and type-checking

```bash
pytest                     # unit tests only (mocked/faked I/O, no live services needed)
pytest -m integration      # integration tests against the docker-compose stack (must be up)

black src tests scripts
ruff check src tests scripts
mypy src tests scripts
```
