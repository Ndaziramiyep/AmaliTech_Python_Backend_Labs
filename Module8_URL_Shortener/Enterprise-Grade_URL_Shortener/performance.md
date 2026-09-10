# Performance: Before vs. After

This document measures the actual impact of this platform's performance
features — database indexing, Redis caching, code-level profiling, and
Gunicorn process tuning — with real before/after numbers, not estimates.

**Methodology**: every number below comes from a script actually run
against this project's own dev containers (Postgres 16 / Redis 7, the same
ones `docker-compose.yml` starts), on this development machine (12 logical
cores, Windows host, Python 3.14, `redis-py` 5.0.1). All benchmark data was
deleted and all schema changes reverted immediately after each run — no
seeded rows or dropped indexes were left behind. Absolute millisecond
values are specific to this machine; the **relative speedups** (Nx faster)
are the number that generalizes. Exact scripts are in the
[Reproducing These Numbers](#reproducing-these-numbers) section at the
bottom so anyone can re-run them.

## Table of Contents

- [1. Database Indexing](#1-database-indexing)
- [2. Redis Caching](#2-redis-caching)
- [3. Code Profiling](#3-code-profiling)
- [4. Gunicorn Process Tuning](#4-gunicorn-process-tuning)
- [Summary](#summary)
- [Reproducing These Numbers](#reproducing-these-numbers)

---

## 1. Database Indexing

**Where**: analytics-service's `ClickEvent` model (`short_code`,
`owner_id` — both already `db_index=True` in the current schema) backs
every analytics query: `UrlClickStatsView`, `DetailedAnalyticsView`, and
the internal cascade-delete on URL removal all filter on this exact
`(short_code, owner_id)` pair.

**What was measured**: 200,000 `ClickEvent` rows were seeded (500 distinct
short codes × 100 owners, realistic cardinality for a busy link), then the
same query DRF's views actually run —
`ClickEvent.objects.filter(short_code=X, owner_id=Y)` — was executed 200
times with random `(X, Y)` pairs, once with the existing indexes in place,
and once with them dropped (`DROP INDEX`) to simulate what this table
would look like without them. The indexes were recreated immediately after.

| Metric                     | Before (no index) | After (indexed)    | Improvement       |
|-----------------------------|--------------------|---------------------|--------------------|
| Avg query time (200 runs)   | 16.435 ms/query    | 2.827 ms/query      | **5.8x faster**    |
| Total time for 200 queries  | 3,287.0 ms         | 565.3 ms            | **5.8x faster**    |
| Query plan                  | `Seq Scan` (full table scan) | `Bitmap Heap Scan` (index-driven) | — |
| Rows scanned per query      | 200,019 (the whole table) | 3 (only matching rows) | — |

**Real `EXPLAIN ANALYZE` output**, same query, same data, index dropped vs.
present:

```text
-- BEFORE: indexes dropped
Seq Scan on analytics_clickevent  (cost=0.00..2618.20 rows=1 width=1638) (actual time=11.928..26.491 rows=3 loops=1)
  Filter: (((short_code)::text = 'NbrnTP'::text) AND (owner_id = 1))
  Rows Removed by Filter: 200019
Planning Time: 0.417 ms
Execution Time: 26.517 ms
```

```text
-- AFTER: indexes present (current schema)
Bitmap Heap Scan on analytics_clickevent  (cost=17.56..21.57 rows=1 width=1638) (actual time=0.419..0.426 rows=3 loops=1)
  Recheck Cond: (((short_code)::text = 'NbrnTP'::text) AND (owner_id = 1))
  Heap Blocks: exact=3
  ->  BitmapAnd  (cost=17.56..17.56 rows=1 width=0) (actual time=0.389..0.390 rows=0 loops=1)
        ->  Bitmap Index Scan on analytics_clickevent_short_code_0e5fc64a_like  (cost=0.00..8.65 rows=49 width=0) (actual time=0.071..0.071 rows=399 loops=1)
              Index Cond: ((short_code)::text = 'NbrnTP'::text)
        ->  Bitmap Index Scan on analytics_clickevent_owner_id_50c21af4  (cost=0.00..8.65 rows=49 width=0) (actual time=0.278..0.278 rows=2004 loops=1)
              Index Cond: (owner_id = 1)
Planning Time: 0.658 ms
Execution Time: 0.493 ms
```

**Why it matters**: without the index, Postgres has to read and filter
*every* row in the table for every single analytics request — the cost
scales linearly with total click volume across the whole platform, not
just with one owner's clicks. With the index, the cost only scales with how
many clicks that one short code/owner has. The gap only widens as the table
grows past 200k rows.

## 2. Redis Caching

**Where**: url-service's `_resolve_short_code` (called on every redirect —
the single hottest path in the platform) is cache-first: a Redis hit
returns immediately, a miss falls back to `url_db` and repopulates the
cache (`url_shortener/caching.py`).

**What was measured**: 500 resolutions of the same short code, once with
the cache forcibly evicted before *every* call (simulating "no cache" — a
`url_db` read on every request), and once with the cache warmed once up
front and left alone (the platform's actual steady-state behavior).

| Metric                  | Before (cache bypassed, `url_db` every time) | After (warm Redis cache) | Improvement    |
|--------------------------|-----------------------------------------------|----------------------------|-----------------|
| Avg lookup time (500 runs) | 2.092 ms/lookup                              | 0.360 ms/lookup            | **5.8x faster** |
| Total time for 500 lookups | 1,046.0 ms                                   | 180.1 ms                   | **5.8x faster** |

**Why it matters**: `_resolve_short_code` runs synchronously in the
request/response path of the platform's single most frequent
endpoint — the public redirect. Every millisecond shaved off it is a
millisecond off *every* redirect, platform-wide. Unlike the indexing case,
this gap doesn't widen with data volume (Redis lookup is O(1) regardless of
how many URLs exist) — it's a flat, permanent tax removed from the hot path.

## 3. Code Profiling

Indexing and caching are both structural fixes — profiling is different:
it's not a fix, it's the *tool* that tells you what to fix. The honest
before/after here isn't a speed number, it's **certainty**:

| | Before profiling | After profiling |
|---|---|---|
| Where does `LoginView.post` spend its time? | Unknown — "login feels fine" or "login feels slow" is a guess | **Measured**: `pbkdf2_hmac` (Django's password hasher) is 0.243s of a 0.384s request — **63%** of total time, and it's the *correct* place for that cost to live (security, not a bug) |
| Where does `_tokens_for_user` spend its time? | Unknown | **Measured**: `str(access)` — JWT signing/serialization — is **98.2%** of that function's 0.0188s runtime; every other line combined is under 2% |

Real `logs/profiling.log` output from running auth-service's test suite
with `ENABLE_PROFILING=true` (see
[Profiling](README.md#-performance-tuning) in the README for how to
reproduce this):

```text
[line_profiler] accounts.api.views._tokens_for_user — 2026-09-10 15:32:27
Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    36         1       1567.0   1567.0      0.8      refresh = RefreshToken.for_user(user)
    45         1        664.0    664.0      0.4      access = refresh.access_token
    52         1     185360.0 185360.0     98.2          'access': str(access),
    53         1       1147.0   1147.0      0.6          'refresh': str(refresh),
```

```text
[cProfile] accounts.api.views.LoginView.post — 2026-09-10 15:32:27
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.243    0.243    0.243    0.243 {built-in method _hashlib.pbkdf2_hmac}
```

**Why it matters**: without this, "make login faster" is a guess aimed at
the whole request. With it, the guess is gone — the data says password
hashing (which should stay slow, that's what makes it secure against
brute-force) dominates login, while JWT serialization dominates token
issuance. That's the difference between optimizing blind and optimizing the
one line that's actually 98% of the cost.

## 4. Gunicorn Process Tuning

**Honesty note**: Gunicorn is Linux-only (it imports `fcntl`), and Docker
wasn't reachable in this environment when this document was written
(`docker ps` timed out — the daemon wasn't responding), so the numbers
below are a **capacity calculation from the actual configured values**, not
a live load-test. See [Reproducing These Numbers](#reproducing-these-numbers)
for the exact commands to get a real measured number once Docker is
available — this section should be the first one updated with a live
number when it is.

**Before** (the platform's original `Dockerfile` command): `gunicorn
Config.wsgi:application --bind 0.0.0.0:8000` — no `-w`/`--workers` flag, so
Gunicorn defaults to **1 sync worker**, meaning exactly **1 request
in flight at a time** per container; every other concurrent request queues
behind it, however long it's blocked (a slow `url_db` query, a slow
external call).

**After** (current `gunicorn.conf.py`, defaults from a 12-core dev
machine): `workers = (2 × 12) + 1 = 25`, `worker_class = "gthread"`,
`threads = 4` → up to **25 × 4 = 100 requests genuinely in flight at
once**, before any request has to queue at all — a **100x** increase in
theoretical concurrent capacity from configuration alone, no code changes.
(A smaller production container, e.g. 2 CPUs, would compute
`workers = 5`, `5 × 4 = 20` in flight — still a 20x jump off the same
un-configured baseline.)

| | Before (unconfigured) | After (tuned, this machine) |
|---|---|---|
| Workers | 1 (Gunicorn's default) | 25 (`(2 × 12 cores) + 1`) |
| Threads/worker | 1 (`sync`) | 4 (`gthread`) |
| Concurrent requests before queuing | 1 | 100 |
| Worker recycling | Never (a memory leak runs forever) | Every ~1,000 requests (`GUNICORN_MAX_REQUESTS`) |

## Summary

| Feature | Metric | Before | After | Improvement |
|---|---|---|---|---|
| DB indexing (analytics) | Avg query time | 16.435 ms | 2.827 ms | **5.8x faster** |
| Redis caching (url-service) | Avg lookup time | 2.092 ms | 0.360 ms | **5.8x faster** |
| Profiling | Time to locate a bottleneck | Guesswork | One log line, exact % | Qualitative |
| Gunicorn tuning | Concurrent requests/container | 1 | 100 (this machine) | **100x capacity** (calculated, not load-tested — see note above) |

## Reproducing These Numbers

Both scripts live in [`benchmarks/`](benchmarks/) at the project root —
deliberately outside any service's own codebase, since they seed data and
drop indexes and have no business shipping in the app itself. Both are
self-contained and clean up everything they touch, safe to re-run against
a local dev environment (needs that service's own Postgres/Redis running,
e.g. via `docker compose up -d <db-service> redis` from within it — see the
README's [Setup Instructions](README.md#-setup-instructions)):

```bash
# 1. Indexing benchmark (analytics-service) — seeds 200k rows, drops/restores
#    the real indexes, deletes all seeded rows when done.
cd services/analytics-service
POSTGRES_HOST=localhost POSTGRES_PORT=5435 python ../../benchmarks/bench_index.py

# 2. Cache benchmark (url-service) — creates/deletes one benchmark Url row
#    and its cache entry.
cd services/url-service
POSTGRES_HOST=localhost POSTGRES_PORT=5436 REDIS_URL=redis://127.0.0.1:6380/1 python ../../benchmarks/bench_cache.py
```

**Expect the exact multiplier to vary run-to-run** (background load on the
machine, Postgres's query planner occasionally choosing a parallel seq scan
instead of a plain one for the "before" case, etc.) — reruns of these two
scripts while writing this document landed anywhere from 4.9x–6.9x. The
conclusion doesn't change: both consistently land in the same
mid-single-digit-multiple range, never close to 1x.

For a **real** (not calculated) Gunicorn concurrency number once Docker is
available:

```bash
cd services/url-service && docker compose up --build -d
# Baseline: force a single worker
docker compose exec url-service sh -c "GUNICORN_WORKERS=1 GUNICORN_WORKER_CLASS=sync kill -HUP 1"
# Load-test both configurations with wrk or ab, e.g.:
wrk -t4 -c100 -d30s http://localhost:8002/abc123/
```
