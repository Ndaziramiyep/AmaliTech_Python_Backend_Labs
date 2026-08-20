# Social Media Lab

A small social-media backend used to practice relational schema design,
transactions, caching, and query tuning. Clean-architecture layering:
domain (pure dataclasses + Protocols) → repositories (Postgres access) →
services (transactions + side effects) → CLI (composition root).

## Schema

Five tables — `users`, `posts`, `comments`, `followers`, `likes` — described
in full, with 3NF justification and indexing rationale, in
[docs/schema_design.md](docs/schema_design.md).

## Setup

```bash
docker compose up -d              # Postgres, Redis, Mongo
python -m venv .venv
.venv/Scripts/activate             # .venv/bin/activate on macOS/Linux
pip install -e .
python scripts/apply_migrations.py
```

Copy `.env.example` to `.env` to point at anything other than the
docker-compose defaults — it's loaded automatically, no manual `export`
needed. Note the compose file maps Postgres/Redis/Mongo to host ports
5433/6380/27018 rather than their usual 5432/6379/27017 — this sidesteps a
common conflict where a locally installed Postgres, Redis-compatible (e.g.
Memurai), or Mongo service is already bound to the standard port and
silently intercepts the container's traffic on `localhost`.

## Running the CLI

Either the installed console script:

```bash
social-cli register alice alice@example.com
social-cli register bob bob@example.com
social-cli follow 1 2
social-cli post 2 "hello, world"
social-cli comment 1 1 "nice post"
social-cli like 1 1
social-cli timeline 1
```

or `python main.py <command> ...` — the same CLI, but runnable straight from
the repo root without `pip install -e .` (it puts `src/` on `sys.path`
itself), e.g. `python main.py timeline 1`.

## Tests

```bash
pytest tests/unit          # fakes only, no infrastructure required
pytest tests/integration   # requires `docker compose up -d` first; skips
                            # automatically if Postgres isn't reachable
```
