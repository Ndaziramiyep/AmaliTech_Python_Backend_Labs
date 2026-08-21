# How This Project Works

This is a walkthrough of the actual code: what each folder does, how a
request moves through the layers, and why the boundaries are drawn where
they are. See [README.md](../README.md) for setup/run instructions and
[schema_design.md](schema_design.md) / [er_diagram.md](er_diagram.md) for
the database design itself. This file is about the *application* on top of
that database.

## The big idea: four layers, one direction of dependency

```text
domain        pure dataclasses + Protocols — no I/O, no driver imports
  ↑
repositories  Postgres access (one table or query each), no business logic
  ↑
services      one transaction + side effects (activity log, cache) per use case
  ↑
cli           composition root — wires real Postgres/Redis/Mongo, dispatches commands
```

The arrow means "depends on", read bottom-to-top: `cli` depends on
`services`, which depends on `repositories` and `domain`, which depend on
nothing else in this project. Nothing above the line ever reaches back
down — `domain` never imports `psycopg2`, a `repository` never opens a
transaction, and a `service` never writes SQL. This is what makes the unit
tests possible without a real database (see [Tests](#tests) below).

## Where each piece lives

```text
src/social/
  domain/
    models.py       User, Post, Comment, Follower, Like — frozen dataclasses
    interfaces.py   Protocols: UserRepository, PostRepository, ..., Cache,
                     ActivityLogger, UnitOfWork
  repositories/
    user_repository.py, post_repository.py, comment_repository.py,
    follower_repository.py, like_repository.py, feed_repository.py
                     one Postgres*Repository class per table (+ the feed join)
  services/
    user_service.py, post_service.py, comment_service.py, follow_service.py,
    like_service.py, feed_service.py, cache_keys.py
                     one *Service class per use case
  infrastructure/
    db/pool.py             PostgresConnectionPool — wraps psycopg2's ThreadedConnectionPool
    db/unit_of_work.py     PostgresUnitOfWork — one connection+cursor per transaction
    cache/redis_client.py  RedisCache — implements the Cache protocol
    activity/mongo_activity_logger.py
                            MongoActivityLogger — implements the ActivityLogger protocol
  cli/
    __main__.py     App (composition root) + argparse subcommands + main()
    interactive.py  menu-driven REPL, calls the same App/services
  config.py         Settings dataclass, loaded from .env via python-dotenv
```

Everything under `domain/` is inert — no network calls, no SQL, nothing
that can fail at runtime except a bad constructor argument. Everything
under `repositories/` and `infrastructure/` is where I/O actually happens.
`services/` is the only place business rules and side-effect ordering live.
`cli/` is the only place that decides *which* real infrastructure to use.

## The three data stores and why each exists

| Store    | What it holds                                   | Why this store |
|----------|--------------------------------------------------|----------------|
| Postgres | users, posts, comments, followers, likes          | relational data with real constraints (uniqueness, foreign keys, composite PKs) and the need for multi-statement transactions |
| Redis    | cached timeline JSON, keyed `timeline:<user_id>`  | the feed query is a join across two large-ish tables; caching it avoids re-running it on every timeline view |
| MongoDB  | an append-only `activity_log` collection          | a write-once audit trail (`user_registered`, `post_created`, `user_followed`, `post_liked`, `comment_created`) that doesn't need relational integrity and shouldn't block or be rolled back by the Postgres transaction it's logging |

Locally, all three run via `docker-compose.yml` (see README). The app
doesn't care whether a store is containerized or not — it only knows the
connection details assembled from `.env`.

## Anatomy of a request: `social-cli follow 1 2`

This is the clearest example because it touches all three stores. Trace it
top to bottom:

1. **`cli/__main__.py: main()`** parses `follow 1 2` into
   `args.follower_id=1, args.followee_id=2`, builds an `App()`, and calls
   `app.follows.follow(1, 2)`.

2. **`cli/__main__.py: App.__init__`** (the composition root) already built
   everything `follow()` needs, once, at startup:
   - a `PostgresConnectionPool` from `settings.postgres_dsn`
   - `uow_factory = lambda: PostgresUnitOfWork(pool)` — a *factory*, not a
     single shared connection, so every service call gets its own
     transaction
   - a `RedisCache(settings.redis_url)`
   - a `MongoActivityLogger(settings.mongo_uri, settings.mongo_db_name)`
   - `FollowService(uow_factory, PostgresFollowerRepository(), activity_logger, cache)`

3. **`services/follow_service.py: FollowService.follow()`** runs three
   steps in a specific, deliberate order:
   ```python
   with self._unit_of_work_factory() as uow:
       follower = self._follower_repository.create(uow.cursor, follower_id, followee_id)
       uow.commit()

   self._activity_logger.log("user_followed", {...})
   self._cache.delete(timeline_cache_key(follower_id))
   return follower
   ```
   - Step 1 (Postgres insert + commit) is the only part wrapped in the
     `with` block — that block is the *entire* ACID boundary. If the insert
     fails (e.g. duplicate follow, since `followers` has a composite
     primary key on `(follower_id, followee_id)`), `__exit__` rolls back
     and nothing below runs.
   - Step 2 (Mongo activity log) happens **after** commit, on purpose —
     see [Why activity logging is outside the transaction](#why-activity-logging-is-outside-the-transaction).
   - Step 3 (Redis cache invalidation) also happens after commit, so a
     follower's next `timeline` call recomputes from Postgres instead of
     serving a feed that predates the new follow.

4. **`repositories/follower_repository.py: PostgresFollowerRepository.create()`**
   is handed `uow.cursor` — it never sees the pool, the connection, or the
   DSN. It just runs one `INSERT ... RETURNING` and maps the row back to a
   `Follower` dataclass. This is what "no business logic" means in
   practice: no ordering decisions, no side effects, just SQL in and a
   dataclass out.

5. **`infrastructure/db/unit_of_work.py: PostgresUnitOfWork`** is what the
   `with` statement is actually managing:
   - `__enter__` pulls a connection from the pool and opens a cursor on it
     (psycopg2 begins the transaction implicitly on the first statement —
     there's no explicit `BEGIN`)
   - `commit()` / `rollback()` delegate straight to the connection
   - `__exit__` rolls back automatically if the block raised, always closes
     the cursor, and returns the connection to the pool — `discard=True` if
     even the rollback failed, so a connection left in a bad state is
     closed instead of recycled

6. Back in `main()`, the returned `Follower` dataclass is printed.

The same shape — one `with unit_of_work_factory() as uow: ... uow.commit()`
block, then side effects after — repeats in every other service
(`UserService.register`, `PostService.create_post`,
`CommentService.create_comment`, `LikeService.like`). `FeedService` is the
one exception, described next.

## The one read path with caching: `timeline`

`FeedService.get_timeline()` is cache-aside, not write-through:

```python
key = timeline_cache_key(follower_id)
cached = self._cache.get(key)
if cached is not None:
    return [_post_from_dict(entry) for entry in json.loads(cached)]

with self._unit_of_work_factory() as uow:
    posts = self._feed_repository.get_timeline(uow.cursor, follower_id, limit)

self._cache.set(key, json.dumps([_post_to_dict(p) for p in posts]), self._ttl_seconds)
return posts
```

- On a cache hit, Postgres is never touched — the JSON blob in Redis is
  deserialized straight back into `Post` dataclasses.
- On a miss, `PostgresFeedRepository.get_timeline()` runs the actual join
  (`posts JOIN followers ON followers.followee_id = posts.author_id WHERE
  followers.follower_id = %s`, indexed by `idx_posts_author_created_at` —
  see [schema_design.md](schema_design.md) for the `EXPLAIN ANALYZE`), then
  the result is cached with a TTL (`REDIS_TIMELINE_TTL_SECONDS`, default 60s).
- Cache invalidation is *event-driven, not TTL-only*: `FollowService.follow`
  deletes `timeline:<follower_id>` the moment a new follow edge commits, so
  a miss on that key means either "never cached" or "just invalidated by a
  new follow" — never "stale because someone posted." New posts from an
  already-followed author don't invalidate anything; the TTL is what bounds
  *that* kind of staleness. This tradeoff (documented in the module
  docstring of `feed_service.py`) is deliberate: invalidating every
  follower's cache on every post would be far more write traffic than
  invalidating one cache entry on the much rarer "follow" action.

## Why activity logging is outside the transaction

Every service docstring says some version of: *"the activity log write
happens only after \[the Postgres] transaction has committed, outside the
ACID boundary."* Concretely, in `UserService.register`:

```python
with self._unit_of_work_factory() as uow:
    created = self._user_repository.create(uow.cursor, draft)
    uow.commit()

self._activity_logger.log("user_registered", {"user_id": created.id, "username": username})
return created
```

If `MongoActivityLogger.log()` raised, the user is still registered — the
Postgres commit already happened. This is intentional: the activity log is
best-effort observability (an audit trail), not a correctness requirement.
Making it part of the same transaction would mean a Mongo hiccup could
block someone from registering, which is the wrong failure mode for a
side-channel log. The cost of this choice is that the log can, in
principle, miss an event if the process crashes between `uow.commit()` and
`activity_logger.log()` — accepted deliberately rather than paying for
exactly-once delivery across two different databases.

## The composition root: why `App` exists

`cli/__main__.py: App.__init__` is the *only* place in the codebase that:

- reads `Settings` (via `load_settings()`)
- constructs `PostgresConnectionPool`, `RedisCache`, `MongoActivityLogger`
- constructs every `Postgres*Repository`
- wires them into every `*Service`

Every service constructor takes its dependencies as the `Protocol` types
from `domain/interfaces.py` (`UnitOfWork`, `Cache`, `ActivityLogger`, one
repository Protocol per table), never a concrete `psycopg2`/`redis`/
`pymongo` type. `App` is what supplies the *real* implementations at
runtime. This is why:

- Unit tests (`tests/unit/`) can hand a service a hand-written fake that
  satisfies the same Protocol, with no real Postgres/Redis/Mongo running.
- Integration tests (`tests/integration/`) exercise the real
  `Postgres*Repository` classes directly against a real (throwaway,
  `_test`-suffixed) database, skipping automatically if Postgres isn't
  reachable — they don't go through `App` at all, since they're testing the
  repositories, not the wiring.
- Swapping Redis for another cache, or Mongo for another log sink, only
  ever touches `infrastructure/` and the one line in `App.__init__` that
  constructs it — no service or repository changes.

## Two front ends, one set of services

`cli/__main__.py: main()` branches on `sys.argv`:

- **No arguments** (`python main.py`) → `interactive.run(App())`, a
  menu-driven REPL (`interactive.py`). It logs a user in or registers one,
  then repeats a numbered menu (`create a post`, `follow a user`, `like a
  post`, `comment on a post`, `view my timeline`) until `q`. Anything that
  needs picking a target (which user to follow, which post to like) is
  shown as a numbered list built from `app.users.list_users()` /
  `app.posts.list_recent()` — never typed in as a raw id — via the shared
  `_pick_from()` helper.
- **With arguments** (`python main.py register alice a@b.com`, or the
  installed `social-cli register alice a@b.com`) → the `argparse` subcommand
  dispatch at the bottom of `main()`.

Both front ends call the exact same `App` services
(`app.users.register`, `app.posts.create_post`, etc.) — `interactive.py`
never touches a repository or the database directly. It's purely a
friendlier UI over the same use cases the non-interactive commands expose.

## Tests

```text
tests/unit/         fakes implementing the domain Protocols; no real
                     Postgres/Redis/Mongo. Tests service logic in isolation:
                     e.g. "does FollowService delete the right cache key?"
tests/integration/  real Postgres, via a `<dbname>_test` database created
                     on demand (tests/integration/conftest.py). Every test's
                     `cursor` fixture drops and rebuilds all 5 tables from
                     migrations/*.sql, so it never touches your real data.
                     Skipped automatically (pytest.skip) if Postgres isn't
                     reachable, rather than failing.
```

The layering is what makes `tests/unit/` possible at all: because every
service depends on `Protocol`s and not concrete drivers, a fake `UnitOfWork`
+ fake repository is enough to exercise `FollowService.follow`'s ordering
(insert, then log, then invalidate) without a database in the loop.

## Following a change end-to-end (for future edits)

If you need to add a new field or a new use case, the layers tell you where
each piece goes:

1. **New column on an existing table** → add a migration in `migrations/`,
   update the dataclass in `domain/models.py`, update the repository's SQL
   and `_row_to_*` mapper.
2. **New use case on existing tables** (e.g. "unfollow") → add a method to
   the relevant repository (SQL only), then a method on the matching
   service (transaction + ordering of side effects), then wire it into
   `cli/__main__.py`'s argparse subcommands and/or `interactive.py`'s menu.
3. **New table** → new migration, new dataclass, new `Protocol` in
   `interfaces.py`, new `Postgres*Repository`, new `*Service`, wire it into
   `App.__init__`, expose it via a subcommand/menu entry.
4. **New side-effect store** (e.g. swapping Mongo for something else) →
   implement the `ActivityLogger` Protocol in `infrastructure/`, change the
   one constructor call in `App.__init__`. No service changes needed.

In every case, the dependency arrow only ever points one way — up. A
migration never imports a service; a service never imports the CLI.
