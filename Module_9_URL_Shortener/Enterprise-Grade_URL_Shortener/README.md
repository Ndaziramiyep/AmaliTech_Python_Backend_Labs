# Enterprise-Grade URL Shortener — Microservices

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-REST%20Framework-A30000)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-Educational-lightgrey)

A URL shortener platform split into four independently deployable Django REST
Framework services. Each has its own database (or none at all, for the
stateless ones), its own Docker image, and its own `docker-compose.yml` —
every service builds, runs, and is started entirely on its own; there is no
root-level orchestration file tying them together, by design. An optional
nginx **API gateway** (`gateway/`) can front the three client-facing services
at a single port — see [API Gateway](#-api-gateway) — but every service is
still fully usable on its own port with the gateway never started at all.

| Service               | Port   | Owns                                    | Responsibility                                                                          |
|-----------------------|--------|------------------------------------------|------------------------------------------------------------------------------------------|
| **auth-service**      | `8001` | `auth_db` (Users)                       | Register, log in, issue/refresh JWTs                                                    |
| **url-service**       | `8002` | `url_db` + Redis + Celery worker/beat   | Create short URLs, resolve/redirect, report click events, nightly-archive expired URLs  |
| **analytics-service** | `8003` | `analytics_db` + Redis + Celery worker  | Record click events (write-behind via Celery), serve click stats                        |
| **preview-service**   | `8004` | nothing (stateless)                     | Internal-only: fetches a destination page's title/description/favicon for url-service   |
| **gateway** *(optional)* | `8080` | nothing (stateless nginx)            | Single entry point: routing, centralized auth, rate limiting, docs/admin/health fan-out |

```
┌──────────────┐      register/login       ┌──────────────┐
│   client     │ ─────────────────────────▶│ auth-service │
│ (browser/    │                            │   :8001      │
│  curl/etc.,  │◀──────── JWT ──────────────┘──────────────┘
│  optionally  │
│  via the     │  Bearer JWT               ┌──────────────┐   record_click_task    ┌───────────────────┐
│  gateway on  │ ─────────────────────────▶│ url-service  │ ──(Celery, resilient  ▶│ analytics-service  │
│  :8080)      │   create / redirect       │   :8002      │   HTTP + retries)      │      :8003         │
└──────────────┘                           └──────┬───────┘                       └───────────────────┘
                                                    │ fetch_url_preview_task
                                                    │ (Celery, resilient HTTP + retries)
                                                    ▼
                                            ┌───────────────────┐
                                            │  preview-service   │
                                            │       :8004        │
                                            │ (fetches the       │
                                            │  destination page) │
                                            └───────────────────┘
```

## 📑 Table of Contents

- [Features](#-features)
- [Technology Stack](#️-technology-stack)
- [Prerequisites](#-prerequisites)
- [Setup Instructions](#-setup-instructions)
- [API Gateway](#-api-gateway)
- [Resilient HTTP Communication & Service Decoupling](#-resilient-http-communication--service-decoupling)
- [External Service Integration: URL Preview](#-external-service-integration-url-preview)
- [Putting It All Together: A Request's Journey](#-putting-it-all-together-a-requests-journey)
- [Authenticating Requests](#-authenticating-requests)
- [API Usage](#-api-usage)
- [Role-Based Access](#-role-based-access)
- [Testing](#-testing)
- [Database Schema](#️-database-schema)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Troubleshooting](#-troubleshooting)
- [Development Notes](#-development-notes)
- [Production Deployment](#-production-deployment)

## 🚀 Features

- **JWT Authentication** (auth-service): register/login with email + password; access & refresh tokens carry custom `email`, `is_staff`, and `tier` claims
- **Stateless cross-service auth**: url-service and analytics-service verify JWTs using a secret shared with auth-service — no network call back to auth-service, no local Users table, no coupling
- **Role-Based Access** (url-service): a URL's owner or a staff/admin user can update, delete, or list it — anyone else gets a 403, enforced from the token's `is_staff` claim alone
- **Tiered Permissions** (auth-service issues, url-service enforces): every user has a `tier` — Free, Premium, or Admin. Premium/Admin unlocks custom aliases; each tier gets its own daily rate limit
- **Rate Limiting**: register/login are throttled per-IP against brute-force; url-service's write endpoints are throttled per-user at a rate that scales with tier (Free: 100/day, Premium/Admin: 1000/day)
- **URL Shortening & Redirect** (url-service): short codes (or a Premium custom alias) backed by PostgreSQL, cached in Redis for fast lookups (cache-first, DB on a miss, invalidated on every update); supports tags, expiry, activation toggling, and per-link metadata
- **Click Analytics** (analytics-service): every redirect through url-service is reported as a click event and persisted write-behind by a Celery worker (never written inline in the request); owners can query per-link and per-account click stats
- **URL Preview** (preview-service, called by url-service): every newly-created short URL gets its destination page's title, meta-description, and favicon fetched and stored automatically, in the background — an owner-supplied value for any of those always wins over the fetched one. See [External Service Integration: URL Preview](#-external-service-integration-url-preview)
- **API Gateway** (`gateway/`, optional): a single nginx entry point in front of the three client-facing services — path-based routing, centralized JWT verification (`auth_request` to auth-service, once per request, instead of every service verifying independently), per-IP rate limiting, and fan-out routes for each service's docs/admin/health under an unambiguous gateway path — see [API Gateway](#-api-gateway)
- **Resilient HTTP + Service Decoupling** (url-service → analytics-service and preview-service): click/delete/preview requests are handed to a Celery task (broker-backed queue), not called synchronously from the request — a create, redirect, or delete always returns immediately, whether or not the downstream service is up. Each task's HTTP client retries transient failures with backoff, and a circuit breaker fails fast (no network attempt) once the downstream service has been down for several consecutive calls, instead of piling up slow, doomed requests; Celery itself retries the whole task with backoff if it's down for longer than that. preview-service adds one more layer: a *per-domain* circuit breaker around the arbitrary destination sites it fetches, since one dead site shouldn't make previews of every other site fail too
- **Nightly Cleanup** (url-service, Celery Beat): a scheduled job archives every URL past its `expires_at` (`is_archived=True`, deactivated, evicted from cache) once a day
- **Structured Logging**: every service logs JSON lines to stdout, with 500-level errors (`django.request`) and security warnings (`django.security`, plus app-level warnings like a rejected internal-key or unauthorized write attempt) always captured
- **Health Checks**: `GET /health/` on url-service, analytics-service, and preview-service verifies database (and, except for preview-service, Redis) connectivity, returning 503 if either is down
- **Database-per-service**: each service has its own Postgres container/database — no service can query another's tables
- **API Documentation**: each service serves its own interactive Swagger UI
- **Docker Support**: every service has its own Dockerfile/image and its own `docker-compose.yml`, and is started standalone — `cd services/<name> && docker compose up --build`

## 🛠️ Technology Stack

- **Framework**: Django 5.0 + Django REST Framework, in all three services
- **Authentication**: JWT via `djangorestframework-simplejwt` (issued by auth-service, verified statelessly elsewhere)
- **Database**: PostgreSQL — a separate container per service
- **Cache**: Redis (`django-redis`), used by url-service for URL lookups
- **Background Tasks**: Celery, in url-service (nightly Celery Beat archive job) and analytics-service (write-behind click persistence) — each with its own Redis broker
- **Logging**: structured JSON to stdout (`logging_utils.JSONFormatter`) in every service that runs Celery
- **API Documentation**: drf-spectacular (OpenAPI/Swagger) per service
- **Server**: Gunicorn (production)
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized setup, or to run Postgres/Redis locally)

## 🔧 Setup Instructions

There's no root-level `.env` and no root-level `docker-compose.yml` — each
service under `services/` is entirely self-contained: its own `Dockerfile`,
its own `docker-compose.yml`, and its own `.env`/`.env.example` (secrets
included). Every service is started on its own, in its own terminal.

`docker-compose.yml` (per service) only sets env vars Docker itself actually
needs: the Postgres image's own `POSTGRES_DB`/`POSTGRES_USER`/
`POSTGRES_PASSWORD`, explicitly as `KEY: ${KEY}` (nothing hardcoded — Compose
resolves each from that service's own `.env` file in the same directory, its
normal automatic lookup). The app container gets **no** `environment:` block
at all — its `Dockerfile` already `COPY`s that service's own `.env` into the
image, and Django reads it directly at startup (`Config/settings.py`), so
Docker doesn't need to pass anything through separately.
`POSTGRES_HOST`/`POSTGRES_PORT` (and, for url-service, `REDIS_URL`/
`ANALYTICS_SERVICE_URL`/`CELERY_BROKER_URL`; for analytics-service,
`CELERY_BROKER_URL`) are set in `.env` to the docker-network values directly
(e.g. `POSTGRES_HOST=auth-db`), since these services are meant to run in
Docker — see the note on running a service locally instead, in Option 2 below.

> Each service's app defaults to its own host port (`8001`/`8002`/`8003`)
> whether started via Docker or `manage.py runserver`, and whether run via
> their own `docker-compose.yml` or locally — so don't run the same service
> both ways at once, but the three *different* services (auth, url, analytics)
> are meant to all be running at the same time, each on its own port, for the
> platform to actually work end to end.

### Option 1: Run with Docker (Recommended)

1. **Copy each service's env file** (only needed once — real `.env` files are
   gitignored, so if they're already present you can skip this)
   ```bash
   cp services/auth-service/.env.example services/auth-service/.env
   cp services/url-service/.env.example services/url-service/.env
   cp services/analytics-service/.env.example services/analytics-service/.env
   cp services/preview-service/.env.example services/preview-service/.env
   ```
   `JWT_SECRET_KEY` must be identical across auth-service, url-service, and
   analytics-service (preview-service doesn't use JWTs at all — see [External
   Service Integration: URL Preview](#-external-service-integration-url-preview));
   `INTERNAL_API_KEY` must be identical across url-service, analytics-service,
   and preview-service. The `.env.example` files already ship with matching
   placeholder values — change them together if you change them at all.

   Cross-service calls (url-service → analytics-service, url-service →
   preview-service) need one more one-time step, regardless of whether you
   ever start the gateway container itself (step 4 below) — the shared
   network they run on:
   ```bash
   docker network create url_shortener_gateway   # one-time
   ```

2. **Build and start each service, in its own terminal**
   ```bash
   cd services/auth-service && docker compose up --build
   cd services/url-service && docker compose up --build
   cd services/analytics-service && docker compose up --build
   cd services/preview-service && docker compose up --build
   ```
   Each command also starts that service's own Postgres, Redis, and Celery
   worker where it has one (plus Celery Beat, for url-service's nightly
   archive job) — preview-service has none of these, just the app container
   itself (see [External Service Integration: URL
   Preview](#-external-service-integration-url-preview)). url-service still
   works fine if analytics-service or preview-service isn't running yet —
   click/delete events and preview fetches are queued via Celery
   (`record_click_task`/`delete_click_events_task`/`fetch_url_preview_task`)
   and retried with backoff until each is reachable, instead of failing the
   redirect/create (see `clients/analytics_client.py`,
   `clients/preview_client.py`, and `tasks.py`).
   `--build` matters here specifically because `.env` is baked into the image
   at build time — if you edit a service's `.env` after already building it
   once, run `docker compose up --build` again (not just `up`) so the new
   values actually take effect.

3. **Access each service**
   - auth-service: http://localhost:8001/docs/
   - url-service: http://localhost:8002/docs/
   - analytics-service: http://localhost:8003/docs/
   - preview-service: http://localhost:8004/docs/ (internal-only in practice — see [External Service Integration: URL Preview](#-external-service-integration-url-preview) — but its Swagger UI is still reachable directly for exploring the contract)
   - Django admin (per service): `:8001/admin/`, `:8002/admin/`, `:8003/admin/`
   - Health check: `:8002/health/`, `:8003/health/`, `:8004/health/` — `200` if database (and, except for preview-service, Redis) is reachable, `503` otherwise

4. **Optional: bring up the API gateway** — a single entry point on `:8080` for the three client-facing services (see [API Gateway](#-api-gateway) for the full routing table and resilience patterns)
   ```bash
   cp gateway/.env.example gateway/.env           # INTERNAL_SERVICE_TOKEN must match auth-service's
   cd gateway && docker compose up -d
   ```
   Each service's own `docker-compose.yml` already joins the
   `url_shortener_gateway` network from step 1 under a fixed alias (`auth`,
   `shortener`, `analytics`, `preview`) once it's up. Skipping this step
   (the gateway container itself) is fine; nothing above depends on it —
   only the network from step 1 does.

### Option 2: Run a Service Locally (Without Docker)

Each service under `services/` is a self-contained Django project, using the
same `.env` file from Option 1 above — but that file's `POSTGRES_HOST`
(`auth-db`/`url-db`/`analytics-db`) and, for url-service, `REDIS_URL` /
`ANALYTICS_SERVICE_URL` / `PREVIEW_SERVICE_URL` / `CELERY_BROKER_URL` (and
for analytics-service, `CELERY_BROKER_URL`), are docker-network addresses,
only resolvable from inside Docker's network. Running `manage.py`/`celery`
directly on your machine instead, override them at the shell first (they
take priority over `.env` without editing it):

```bash
POSTGRES_HOST=localhost POSTGRES_PORT=5434 python manage.py runserver          # auth-service

# url-service
POSTGRES_HOST=localhost POSTGRES_PORT=5436 REDIS_URL=redis://127.0.0.1:6380/1 CELERY_BROKER_URL=redis://127.0.0.1:6380/2 ANALYTICS_SERVICE_URL=http://localhost:8003 PREVIEW_SERVICE_URL=http://localhost:8004 python manage.py runserver
POSTGRES_HOST=localhost POSTGRES_PORT=5436 CELERY_BROKER_URL=redis://127.0.0.1:6380/2 ANALYTICS_SERVICE_URL=http://localhost:8003 PREVIEW_SERVICE_URL=http://localhost:8004 celery -A Config worker -l info    # + separate terminal for Beat: celery -A Config beat -l info

# analytics-service
POSTGRES_HOST=localhost POSTGRES_PORT=5435 CELERY_BROKER_URL=redis://127.0.0.1:6381/0 python manage.py runserver
POSTGRES_HOST=localhost POSTGRES_PORT=5435 CELERY_BROKER_URL=redis://127.0.0.1:6381/0 celery -A Config worker -l info

# preview-service — no database/Redis override needed at all: it uses
# SQLite (no Docker-network address to resolve) and has no Celery worker.
python manage.py runserver
```

Skipping the Celery worker still leaves the app itself fully usable — url-service's
nightly archive job and preview fetches just never run (they stay queued),
and analytics-service's `POST /api/v1/events/click/` enqueues clicks that
sit in Redis unprocessed until a worker is started.

1. **Create a virtual environment per service** (dependencies differ slightly
   per service, so don't share one venv across them)
   ```bash
   cd services/auth-service   # or url-service / analytics-service / preview-service
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Start that service's own database and Redis** — using that service's own
   `docker-compose.yml` is easiest, since it starts just the infra without
   also starting the Django app in a container (preview-service has neither,
   so there's nothing to start for it — skip straight to step 3):
   ```bash
   docker compose up -d auth-db                # from services/auth-service/
   docker compose up -d url-db redis            # from services/url-service/
   docker compose up -d analytics-db redis      # from services/analytics-service/
   ```
   Each db container is exposed on the host — `auth-db` on `5434`, `url-db` on
   `5436`, `analytics-db` on `5435` — and each service's own Redis is exposed
   too — url-service's on `6380`, analytics-service's on `6381` — matching the
   `POSTGRES_PORT`/`REDIS_URL`/`CELERY_BROKER_URL` already set in that
   service's `.env`.

3. **Run migrations and start the server on its own port**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser   # optional, for that service's admin
   python manage.py runserver
   ```
   With no addrport argument, `runserver` normally falls back to `8000` for
   every service — `manage.py` here instead defaults it to that service's own
   `PORT` from `.env` (`8001`/`8002`/`8003`/`8004`), so running all four
   locally at once doesn't collide. Pass an addrport explicitly (e.g.
   `runserver 9000`) to override it.

## 🚪 API Gateway

An optional nginx gateway (`gateway/`) fronts the three client-facing
services on a single port, `:8080` (preview-service is internal-only — see
[External Service Integration: URL
Preview](#-external-service-integration-url-preview) — so it's on the same
network for url-service to reach it, but the gateway never routes client
traffic to it). It's a separate `docker-compose.yml`, joined to the same
`url_shortener_gateway` external network each service's own compose file
already declares — bring it up (or not) independently of the services
themselves; nothing above requires it.

**Routing table** (client-facing; service-to-service traffic bypasses the
gateway entirely and calls containers directly):

| Path prefix                      | Routed to          | Notes                                                        |
|-----------------------------------|---------------------|---------------------------------------------------------------|
| `/api/v1/auth/*`                  | auth-service        | Rate-limited tighter than everything else (`auth_limit`)     |
| `/api/v1/urls/*`                  | url-service         | Requires a valid Bearer JWT (see below)                       |
| `/api/v1/analytics/*`             | analytics-service   | Requires a valid Bearer JWT                                    |
| `/api/v1/docs/<service>/`, `/api/v1/schema/<service>/` | that service | Swagger UI/schema, disambiguated per service              |
| `/admin/<service>/`               | that service        | Django admin, disambiguated per service                       |
| `/health/<service>/`              | url-service/analytics-service/preview-service | Same 200/503 contract as calling the service directly |
| `/api/v1/*`, `/`                  | url-service         | Public JSON resolve and the short link itself (e.g. `/abc123`) |
| `/api/v1/internal/*`, `/internal/*`, `/api/v1/preview/` | — (404) | Internal-only endpoints are never reachable through the gateway — preview-service is called by url-service directly, container-to-container, never through here |

**Centralized authentication**: rather than every service verifying JWTs
independently at the edge, protected locations (`/api/v1/urls/`,
`/api/v1/analytics/`) use nginx's `auth_request` to call auth-service's
internal token-validation endpoint once per request. auth-service checks the
JWT and an `X-Internal-Token` (proving the call came from the gateway, not
the public internet), then returns the decoded identity as response headers
(`X-User-Id`, `X-Username`, `X-User-Tier`, `X-User-Is-Premium`), which the
gateway forwards on to url-service/analytics-service as trusted request
headers. A 401/403 from that check short-circuits the request before it ever
reaches url-service or analytics-service.

**Resilience patterns at the gateway**:
- **Rate limiting** — `limit_req_zone` cap traffic per client IP before it
  reaches a backend at all: 5 req/s (burst 10) on auth endpoints, 20 req/s
  (burst 40) everywhere else client-facing. Exceeding it gets a `429`, not a
  slow backend response.
- **Fail-fast timeouts** — `proxy_connect_timeout`/`proxy_send_timeout`/
  `proxy_read_timeout` keep a hung or unreachable backend from tying up a
  gateway connection indefinitely.

See resilient HTTP communication and service decoupling below for the
patterns used *between* services (url-service → analytics-service and
preview-service), independent of whether the gateway is running at all.

### API Versioning

Every client-facing endpoint on every service is namespaced under
`/api/v1/...` — there's no bare, unversioned route anywhere in this API (see
the [routing table](#-api-gateway) above and [API Endpoints](#-api-endpoints)
below). A future breaking change gets its own `/api/v2/...` prefix rather
than mutating `v1`'s contract out from under existing callers; the gateway's
path-based routing (each `location` block matches on the full
`/api/v1/...` prefix) would extend to a second version with an equivalent
set of `/api/v2/...` locations, routed however that version's endpoints
need to be split across services — old and new versions can run side by
side indefinitely.

### CORS for a Frontend (e.g. React)

Every service already has `django-cors-headers` installed and configured
(`CORS_ALLOW_ALL_ORIGINS`/`CORS_ALLOWED_ORIGINS` in each service's `.env` —
see each service's Setup Instructions above), so no new code is needed to
call this API from a browser-based frontend — only correct configuration.
The one subtlety worth calling out: **the gateway itself does not add CORS
headers** — it's a plain reverse proxy, and passes the browser's `Origin`
header straight through unchanged. The response's `Access-Control-Allow-*`
headers are actually added by whichever Django service ends up handling that
specific request (auth-service for `/api/v1/auth/*`, url-service for
`/api/v1/urls/*`, etc.) — so **every** service the frontend talks to, not
just one of them, needs the frontend's origin allowed, even though the
frontend only ever talks to the gateway's single `:8080` origin.

For a React app running on its usual dev-server origin, in each of
auth-service/url-service/analytics-service's `.env`:
```bash
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=http://localhost:3000
```
(`CORS_ALLOW_ALL_ORIGINS=True`, the default in `DEBUG` mode, already works
for local development without this — it's only for a production frontend
origin that this needs to be set explicitly.) No further configuration is
needed for the `Authorization` header specifically — `django-cors-headers`
allows it by default — and no `CORS_ALLOW_CREDENTIALS` setting is needed
either, since auth here is a Bearer token in a header, not a cookie.

### Running it

```bash
docker network create url_shortener_gateway   # one-time
cp gateway/.env.example gateway/.env           # INTERNAL_SERVICE_TOKEN must match auth-service's
cd gateway && docker compose up -d
```

Then use `http://localhost:8080` in place of the individual `:8001`/`:8002`/
`:8003` ports for anything client-facing — e.g. `POST
http://localhost:8080/api/v1/auth/login/` instead of `:8001/api/v1/auth/login/`.

## 🔁 Resilient HTTP Communication & Service Decoupling

url-service is the one place inter-service HTTP calls happen at runtime — it
reports every redirect (and cascades every delete) to analytics-service, and
asks preview-service to fetch a destination page's preview on every create.
In both cases, rather than a synchronous call in the request path, the view
hands the work off to a Celery task
(`record_click_task`/`delete_click_events_task`/`fetch_url_preview_task` in
`url_shortener/tasks.py`), queued on url-service's own Redis broker. Every
one of those tasks shares the same pattern, implemented once in
`url_shortener/clients/resilience.py` and reused by both
`clients/analytics_client.py` and `clients/preview_client.py`:

- **Decoupled from the downstream service's availability**: a create,
  redirect, or delete always returns immediately — success doesn't depend on
  analytics-service or preview-service being reachable, or even running, at
  that instant. If either is down, its task just sits in the queue until a
  worker can deliver it.
- **Retries at two levels**: the HTTP client itself retries a connection
  failure or 5xx response up to 3 times with exponential backoff before
  giving up on that attempt (`resilience.build_retrying_session`); if the
  whole attempt still fails, the *task* is retried by Celery (up to 5 times,
  with backoff and jitter) — so a blip that clears up in seconds is absorbed
  by the HTTP-level retry, while a longer outage is absorbed by the
  task-level retry, without ever blocking the original request either way.
- **Circuit breaker**: after 5 consecutive failures reaching a downstream
  service at all, its client stops attempting the network call for 30
  seconds (raising immediately instead — `resilience.CircuitBreaker`), so a
  sustained outage doesn't pile up slow, doomed connection attempts — then
  lets a single trial call through to check whether it has recovered.
  preview-service additionally runs its own, separate circuit breaker keyed
  *per destination domain* (see [External Service Integration: URL
  Preview](#-external-service-integration-url-preview)) — a distinct
  problem from preview-service itself being down.

None of this is visible to a caller of the create/redirect/delete endpoints
— it's purely about a downstream dependency's uptime never becoming
url-service's problem.

## 🔎 External Service Integration: URL Preview

When a URL is created, url-service doesn't just store it — it also fetches
the destination page's `<title>`, meta-description, and favicon, and stores
those on the same `Url` row (the `title`/`description`/`favicon` fields
already used for owner-supplied metadata — see [Database
Schema](#️-database-schema)). Fetching an arbitrary third-party page is
exactly the kind of unreliable external dependency the resilience patterns
above exist for, so the actual fetch is delegated to a separate, minimal
service, and never allowed to block URL creation.

**preview-service** (`services/preview-service/`) is a small, stateless
Django app with a single internal endpoint, `POST /api/v1/preview/`
(`X-Internal-Key` gated, same contract as analytics-service's internal
endpoint — never reachable through the gateway, see [API
Gateway](#-api-gateway)):
1. url-service's `fetch_url_preview_task` (queued right after `Url.objects.create(...)`
   in `UrlListCreateView.post`) calls preview-service via
   `url_shortener/clients/preview_client.py`.
2. preview-service fetches the destination page itself
   (`preview/fetcher.py`) — with its own retrying session (a transient
   connection failure or 5xx is retried 3 times with backoff) — reads at
   most 1MB of the response (a page's `<head>` is always near the top), and
   parses out the title, `<meta name="description">` (falling back to
   `og:description`), and the best available `<link rel="icon">` (falling
   back to `/favicon.ico`) with BeautifulSoup.
3. **Per-domain circuit breaker (bonus)**: if the *same domain* fails 3
   times in a row, preview-service stops even attempting to fetch it for 60
   seconds, returning `502` immediately instead — deliberately scoped to one
   domain at a time, so a single dead site being retried over and over
   doesn't affect previews for every other site being requested at the same
   time.
4. url-service's task fills in whichever of `title`/`description`/`favicon`
   are still blank on that `Url` — an owner-supplied value on create always
   wins and is never overwritten.

If the destination site is down, or preview-service itself is unreachable,
URL creation still succeeds immediately with those three fields left
`null` — they simply stay `null` until a later retry succeeds, if it ever
does. Nothing about this feature can turn into a reason `POST /api/v1/urls/`
fails or hangs.

## 🧭 Putting It All Together: A Request's Journey

The three sections above (gateway, resilience/decoupling, preview) each
describe one piece in isolation. This walks through two complete, concrete
requests — start to finish, container to container — to show exactly how
those pieces connect. Both assume the gateway is running (see [API
Gateway](#-api-gateway)); without it, skip straight to step 2 and call
url-service's own `:8002` directly instead — every downstream step is
identical either way.

### Walkthrough A — `POST http://localhost:8080/api/v1/urls/`

1. **nginx (gateway, `:8080`) receives the request.** Its `location
   /api/v1/urls/` block matches. Before doing anything else, it applies
   `limit_req zone=api_limit` (rejects with `429` if this client IP is
   over 20 req/s) and fires an internal subrequest to `/internal/verify`.
2. **`/internal/verify` → auth-service.** nginx's `auth_request` forwards
   the caller's `Authorization: Bearer <token>` header, plus its own
   `X-Internal-Token` (proving this call came from the gateway itself), to
   auth-service's `GET /api/v1/auth/internal/token/validate/`. auth-service
   checks both; a failure here (bad token, bad internal token, expired
   token) returns `401`/`403`, which nginx turns into the gateway's own
   `401` response — url-service is **never reached** for an unauthenticated
   or invalid request.
3. **Identity flows back as headers.** On success, auth-service's response
   carries `X-User-Id`/`X-Username`/`X-User-Tier`/`X-User-Is-Premium`; nginx
   captures those (`auth_request_set`) and re-sends them as request headers
   on the *original* request it now proxies to url-service — url-service
   trusts them as-is, the same way it would trust claims it decoded from
   the JWT itself if called directly (no gateway in the path).
4. **url-service (`UrlListCreateView.post`) does the actual work**:
   validates the payload, checks the Free-tier 10-active-URL cap, generates
   a short code, and `Url.objects.create(...)`s the row in `url_db`. It
   caches the short_code → URL/owner lookup in Redis, then calls
   `fetch_url_preview_task.delay(url_obj.id)` — this returns instantly
   (it publishes one message to url-service's own Redis broker; it does
   **not** wait for preview-service). The view returns `201` right away,
   `title`/`description`/`favicon` still `null` in the response body.
5. **Off the request path, a Celery worker in url-service's own container**
   picks up `fetch_url_preview_task` and calls `preview_client.fetch_preview(...)`,
   which:
   - checks its own circuit breaker for preview-service first (skips the
     network call entirely, raising immediately, if preview-service has
     failed 5 times in a row in the last 30s);
   - otherwise `POST`s to preview-service directly, container-to-container
     — `http://preview:8000/api/v1/preview/` — **never through the gateway**
     (the gateway 404s that path on purpose; see [API Gateway](#-api-gateway)'s
     routing table);
   - retries a connection failure or 5xx up to 3 times with backoff before
     giving up on this attempt (`resilience.build_retrying_session`).
6. **preview-service receives the internal call**, checks `X-Internal-Key`,
   then fetches the *actual destination site* (e.g. `https://example.com`)
   with its own retrying session and its own circuit breaker — this one
   keyed **per destination domain**, completely separate from url-service's
   circuit breaker on preview-service itself. It parses the HTML and
   returns `{title, description, favicon}` as JSON (or `502` if the fetch
   ultimately failed).
7. **Back in url-service's task**: on success, it updates the `Url` row —
   only the fields the owner left blank — and the change is visible on the
   next `GET /api/v1/urls/{short_code}/`. On failure, the task itself
   raises, and Celery retries the *whole task* later (up to 5 times, with
   backoff and jitter) — completely independent of, and layered on top of,
   the HTTP-level retry in step 5. If every retry is exhausted, the fields
   just stay `null` forever; nothing else about the URL is affected.

### Walkthrough B — `GET http://localhost:8080/{short_code}/`

1. **Gateway**: matches the catch-all `location /` block (rate-limited,
   no `auth_request` — this route is intentionally public), and proxies
   straight to url-service.
2. **url-service (`RedirectUrlView.get`)**: resolves the code (cache first,
   `url_db` on a miss), 404s if inactive/expired, atomically increments
   `click_count`, and immediately returns `302 Location: <original_url>` —
   the browser is redirected before anything below this line has even
   necessarily started running.
3. **`record_click_task.delay(...)`** is queued (same non-blocking
   `.delay()` as Walkthrough A) with the short code, owner id, and
   request metadata (referrer, user-agent, IP).
4. **url-service's Celery worker** picks it up, geolocates the IP via a
   free public API (best-effort — swallows its own failures, since a
   missing city/country was never worth blocking a click over), then
   calls `analytics_client.record_click(...)` — same
   retry/circuit-breaker/task-retry stack as Walkthrough A, steps 5–7,
   just aimed at analytics-service (`http://analytics:8000`) instead of
   preview-service.
5. **analytics-service** checks `X-Internal-Key`, validates the payload,
   and hands the actual database write to *its own* Celery worker
   (`track_click_task.delay(...)`) — a second, independent write-behind
   step, so analytics-service's own view never blocks on a database write
   either. The click becomes visible via `GET
   /api/v1/analytics/urls/{short_code}/` once that write lands.

Every failure mode in both walkthroughs — analytics-service down,
preview-service down, the destination site down, even the database
briefly unreachable — degrades to "the data arrives late, or never,"
never to "the user-facing request fails or hangs."

## 🔑 Authenticating Requests

Every protected endpoint expects the access token as a **Bearer token** on the
`Authorization` header — that's the one and only place it goes:

```text
Authorization: Bearer <your-access-token>
```

**In Swagger UI** (`:8001/docs/`, `:8002/docs/`, `:8003/docs/`):

1. Register or log in via auth-service's `/api/v1/auth/register/` or `/api/v1/auth/login/` and copy the `access` value from the response.
2. On whichever service's Swagger page you want to call, click the green **Authorize** button (top right), paste just the raw token — no `Bearer` prefix, Swagger adds that — and click **Authorize**.
3. Every "Try it out" call on that page now sends it automatically.

**Via curl / any HTTP client**, set the header directly:
```bash
curl -X POST http://localhost:8002/api/v1/urls/ \
  -H "Authorization: Bearer <your-access-token>" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com"}'
```

The token is only ever issued by auth-service, but url-service and
analytics-service both verify it themselves (see `security/authentication.py`
in url-service, `authentication.py` in analytics-service) and both show the
same Authorize button — this required manually registering
a `drf_spectacular.extensions.OpenApiAuthenticationExtension` for
`StatelessJWTAuthentication`, since drf-spectacular only auto-detects the
stock `JWTAuthentication` class, not a subclass of it.

## 📚 API Usage

### auth-service (`:8001`)

#### 1. Register — `POST /api/v1/auth/register/`
```json
{
  "email": "alice@example.com",
  "password": "StrongPassword123",
  "confirm_password": "StrongPassword123"
}
```
**Response** (201): `{ "id": 1, "email": "alice@example.com", "access": "...", "refresh": "..." }`

#### 2. Login — `POST /api/v1/auth/login/`
```json
{ "email": "alice@example.com", "password": "StrongPassword123" }
```
**Response** (200): same shape as register.

#### 3. Refresh — `POST /api/v1/auth/refresh/`
```json
{ "refresh": "<jwt-refresh-token>" }
```
**Response** (200): `{ "access": "<new-jwt-access-token>" }`

### url-service (`:8002`)

#### 4. Create Short URL — `POST /api/v1/urls/` (requires `Authorization: Bearer <access-token>`)
```json
{ "original_url": "https://www.example.com", "tags": ["news"] }
```
Free tier is capped at 10 **active** URLs (a 403 past that — deactivated ones
don't count); `custom_alias` requires Premium/Admin. `title`, `description`,
`favicon`, `is_active`, `expires_at`, and `tags` are all optional — any of
`title`/`description`/`favicon` you don't supply are fetched from the
destination page in the background (see [External Service Integration: URL
Preview](#-external-service-integration-url-preview)) and populate a moment
after this response, which is why they're `null` below even though the
request above didn't set `is_active`/`expires_at` either.
**Response** (201):
```json
{
  "id": 1,
  "original_url": "https://www.example.com",
  "short_url": "abc123",
  "short_link": "http://localhost:8002/abc123/",
  "custom_alias": null,
  "owner": "alice@example.com",
  "is_active": true,
  "expires_at": null,
  "title": null,
  "description": null,
  "favicon": null,
  "click_count": 0,
  "tags": ["news"],
  "created_at": "2026-08-31T14:00:00Z"
}
```

#### 5. List Your URLs — `GET /api/v1/urls/` (requires `Authorization: Bearer <access-token>`)
Returns only the URLs you own, paginated (`?page=`, `?page_size=`, 20/page by
default) and filterable by exact tag name (`?tag=news`). A staff/admin user
(see [Role-Based Access](#-role-based-access) below) gets every URL from
every owner instead.
**Response** (200): `{ "count": 1, "next": null, "previous": null, "results": [ <same shape as endpoint 4's response> ] }`

#### 6. Retrieve URL Details — `GET /api/v1/urls/{short_code}/` (or a `custom_alias`)

Public — no authentication required. Returns the same full shape as endpoint
4's response (not just the original URL). Returns 404 if the code is
unknown, inactive, or past its `expires_at`.

#### 7. Fully Update a Short URL — `PUT /api/v1/urls/{short_code}/` (requires `Authorization: Bearer <access-token>`)

```json
{ "original_url": "https://www.updated-example.com" }
```
`original_url` is required (a full update); `custom_alias`, `title`, etc. are
still optional. Only that URL's owner, or a staff/admin user, may do this —
anyone else gets a **403 Forbidden**.
**Response** (200): the updated URL, same shape as endpoint 4's response.

#### 8. Partially Update a Short URL — `PATCH /api/v1/urls/{short_code}/` (requires `Authorization: Bearer <access-token>`)

```json
{ "is_active": false }
```
Same ownership rule as PUT, but every field is optional — only what's
submitted gets changed (e.g. deactivating a link without touching anything
else).
**Response** (200): the updated URL, same shape as endpoint 4's response.

#### 9. Delete a Short URL — `DELETE /api/v1/urls/{short_code}/` (requires `Authorization: Bearer <access-token>`)
Only that URL's owner, or a staff/admin user, may do this — anyone else gets
a **403 Forbidden**. Hard-deletes the row and cascades to analytics-service,
removing that code's click history there too, via a queued, retried Celery
task rather than a synchronous call (see [Resilient HTTP Communication &
Service Decoupling](#-resilient-http-communication--service-decoupling) —
see also [Role-Based Access](#-role-based-access)).
**Response** (204): empty body.

#### 10. Redirect — `GET /{short_code}/` (or a `custom_alias`)
Paste directly into a browser: http://localhost:8002/abc123/ → 302 to the
original URL. Returns 404 if inactive or expired. Every successful redirect
increments `click_count` and queues a click event (with best-effort
geolocation) to analytics-service via Celery, so it never delays the
redirect itself and never gets lost if analytics-service is temporarily
down.

### analytics-service (`:8003`, requires `Authorization: Bearer <access-token>`)

#### 11. Click Stats for One Short Code — `GET /api/v1/analytics/urls/{short_code}/`
**Response** (200): `{ "short_code": "abc123", "click_count": 4, "last_clicked_at": "2026-08-31T14:05:00Z" }`
Only counts clicks recorded under your own user id.

#### 12. Your Click Summary — `GET /api/v1/analytics/summary/`
**Response** (200): `[ { "short_code": "abc123", "click_count": 4 }, { "short_code": "xyz789", "click_count": 1 } ]`

#### 13. Detailed Analytics (Premium/Admin only) — `GET /api/v1/analytics/{short_code}/`

Daily time-series click counts plus a city/country geo breakdown. Free tier
gets a **403 Forbidden**. `city`/`country` are `null` for clicks whose IP
couldn't be geolocated (always true for private/local IPs, e.g. local dev).
**Response** (200):
```json
{
  "short_code": "abc123",
  "click_count": 4,
  "time_series": [ { "date": "2026-09-01", "count": 3 }, { "date": "2026-09-02", "count": 1 } ],
  "geo_breakdown": [ { "city": "Kigali", "country": "Rwanda", "count": 3 }, { "city": null, "country": null, "count": 1 } ]
}
```

#### 14. Record Click (internal) — `POST` / `DELETE /api/v1/events/click/`

Called by url-service, not meant for direct/public use — requires the
`X-Internal-Key` header to match `INTERNAL_API_KEY`. `POST` validates the
payload and hands the actual write off to a Celery worker
(`track_click_task.delay(...)`, write-behind — the view itself never writes
to the database) and returns 201 immediately; `DELETE` (body:
`{"short_codes": [...]}`) cascade-deletes click history for those codes,
called when url-service deletes a URL.

#### 15. Health Check — `GET /health/` (url-service, analytics-service)

No authentication required. Verifies the database and Redis are both
reachable and returns `{"status": "ok", "checks": {"database": true, "redis": true}}`
(200), or `{"status": "unavailable", ...}` with whichever check(s) failed set
to `false` (503) otherwise.

## 🔐 Role-Based Access

Anyone can **read** a URL (`GET`, resolve, redirect) — but only its owner or
a staff/admin user can update (`PUT`/`PATCH`), delete, or see it in the
**list** endpoint. This is the classic `IsOwnerOrReadOnly` pattern (DRF's own
tutorial convention): public read, owner-or-admin write.

This is driven by an `is_staff` claim embedded in the JWT at register/login
time (`accounts/api/views.py` in auth-service, mirroring how the `email`
claim already works — see [Stateless JWT verification](#-development-notes)
below), read by url-service's `IsOwnerOrReadOnly` permission
(`url_shortener/api/permissions.py`) without any call back to auth-service.

To make a user an admin, set `is_staff=True` on their row in auth-service's
own Django admin (`http://localhost:8001/admin/`) or via
`python manage.py createsuperuser` — then have them log in again so the new
token carries the updated claim (existing tokens keep whatever `is_staff`
value they were issued with until they expire).

Deleting a URL you own (or any URL, as admin) hard-deletes it in `url_db`
**and** cascades to analytics-service, removing that code's click history
there too — the delete itself runs synchronously, but the cascade is queued
as a Celery task (`delete_click_events_task`), so a slow, unreachable, or
temporarily-down analytics-service never delays the 204 response and never
loses the delete — the task just retries until it lands.

### Tiered Permissions

Every user has a `tier`: `Free`, `Premium`, or `Admin` (default `Free` on
registration). Setting `tier` to `Admin` also grants `is_staff` automatically
(`accounts/models.py`'s `User.save()`); `is_premium` is likewise kept in sync
with `tier == "Premium"`. Change a user's tier the same way as `is_staff` —
via auth-service's Django admin — then have them log in again for a token
carrying the new claim.

What tier unlocks today:

- **`custom_alias`** on `POST`/`PUT`/`PATCH /api/v1/urls/`: Free tier gets a
  400 (`"Custom aliases are a Premium/Admin feature."`); Premium/Admin can
  set one, and it resolves identically to the generated `short_url`
  everywhere (`GET`, redirect, click reporting).
- **Active URL cap**: Free tier is capped at 10 **active** (`is_active=True`)
  URLs — the 11th `POST` gets a 403 until one is deactivated or deleted.
  Premium/Admin is unlimited. Deactivated URLs don't count against the cap.
- **Detailed Analytics** (`GET /api/v1/analytics/{short_code}/` on
  analytics-service): time-series + geo-location breakdown. Free tier gets a
  403 (`IsPremiumOrAdmin`); the basic stats/summary endpoints stay available
  to everyone regardless of tier.
- **Rate limits** (see below) scale with tier.

### Rate Limiting

- **auth-service**: `POST /api/v1/auth/login/` is throttled to **5 requests/minute
  per IP** (`LoginRateThrottle`, scope `login`) — brute-force protection on
  the one endpoint that's actually guessing a password. `POST /api/v1/auth/register/`
  gets a looser 20/minute (`AnonRateThrottle`, scope `anon`) against
  registration spam. Both throttle before any user/tier exists yet, so
  they're necessarily per-IP rather than per-user.
- **url-service**: write endpoints (`POST /api/v1/urls/`,
  `PUT`/`PATCH`/`DELETE /api/v1/urls/{short_code}/`) are throttled per user at a rate
  that scales with their tier claim — Free: 100/day, Premium/Admin: 1000/day
  (`TieredUserRateThrottle` in `url_shortener/api/throttling.py`). Exceeding
  it returns a **429 Too Many Requests**. Reads (list, resolve, redirect)
  aren't throttled.

## 🧪 Testing

Each service has its own test suite:
```bash
cd services/auth-service && python manage.py test
cd services/url-service && python manage.py test
cd services/analytics-service && python manage.py test
cd services/preview-service && python manage.py test
```

## 🗄️ Database Schema

Each model lives in the service that owns it — there are no cross-service
foreign keys, since each service has its own database (see
[Key Design Decisions](#-development-notes)). Where the schema conceptually
wants a foreign key to a row in another service's database, that reference
is stored as a plain denormalized id/value instead (`owner_id`/`owner_email`,
`short_code`).

### auth-service — `User` (`accounts/models.py`, extends `AbstractUser`)

| Field        | Type                                    | Notes                                             |
|--------------|-----------------------------------------|---------------------------------------------------|
| `email`      | `EmailField(unique=True)`               | Overrides `AbstractUser`'s non-unique default     |
| `is_premium` | `BooleanField(default=False)`           | Kept in sync with `tier == "Premium"` on save     |
| `tier`       | `CharField(choices=Free/Premium/Admin)` | Default `Free`; `Admin` also sets `is_staff=True` |

Plus everything `AbstractUser` already provides (`username`, `password`,
`is_staff`, `is_superuser`, `date_joined`, etc.).

### url-service — `Url` and `Tag` (`url_shortener/models.py`)

| Field                             | Type                                    | Notes                                                         |
|-----------------------------------|-----------------------------------------|---------------------------------------------------------------|
| `owner_id`                        | `PositiveIntegerField`                  | Denormalized reference to auth-service's `User.id` -- no FK   |
| `owner_email`                     | `EmailField`                            | Denormalized, same reason                                     |
| `original_url`                    | `URLField`                              | Must start with `http://` or `https://`                       |
| `short_url`                       | `CharField(unique=True, max_length=10)` | The generated 6-character code                                |
| `custom_alias`                    | `CharField(unique=True, null=True)`     | Premium/Admin-only; resolves identically to `short_url`       |
| `is_active`                       | `BooleanField(default=True)`            | `False` makes the link 404 on resolve/redirect (soft-delete)  |
| `expires_at`                      | `DateTimeField(null=True)`              | Past this timestamp, the link 404s on resolve/redirect        |
| `is_archived`                     | `BooleanField(default=False)`           | Set by the nightly `archive_expired_urls` Celery Beat task, not the owner |
| `archived_at`                     | `DateTimeField(null=True)`              | When the archive task swept this URL, if it has been          |
| `title`, `description`, `favicon` | `CharField(null=True)`                  | Owner-supplied on create, or auto-fetched from the destination page by preview-service otherwise — see [External Service Integration: URL Preview](#-external-service-integration-url-preview) |
| `click_count`                     | `PositiveIntegerField(default=0)`       | Incremented atomically by url-service on every redirect       |
| `tags`                            | `ManyToManyField(Tag)`                  | Optional, set via the `tags` field on create/update           |
| `created_at`                      | `DateTimeField(auto_now_add=True)`      | --                                                            |

`Tag` is just `name` (`CharField(unique=True)`).

### analytics-service — `ClickEvent` (`analytics/models.py`)

| Field                    | Type                               | Notes                                                                                                                                |
|--------------------------|------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| `short_code`             | `CharField(max_length=50)`         | Denormalized reference to url-service's `Url` -- no FK; 50 chars to fit a `custom_alias`                                             |
| `owner_id`               | `PositiveIntegerField`             | Denormalized reference to auth-service's `User.id`                                                                                   |
| `referrer`, `user_agent` | `CharField`                        | From the redirecting request's headers                                                                                               |
| `ip_address`             | `GenericIPAddressField(null=True)` | --                                                                                                                                   |
| `city`, `country`        | `CharField(null=True)`             | Populated only if the reporting client supplies them (url-service doesn't do IP geolocation today, so these stay `null` in practice) |
| `clicked_at`             | `DateTimeField(auto_now_add=True)` | --                                                                                                                                   |

> **Caveat**: because `owner_id` is a denormalized integer rather than a
> real foreign key, resetting auth-service's database restarts its id
> sequence from 1 — any `owner_id` values already stored in url_db/analytics_db
> then risk colliding with a *different*, newly-registered user who happens
> to get the same recycled id. This is a known tradeoff of the
> database-per-service split; it isn't an issue in a system that's never had
> auth-service's database reset independently of the others.

## 📁 Project Structure

```
Enterprise-Grade_URL_Shortener/
├── services/
│   ├── auth-service/
│   │   ├── Config/                # settings (AUTH_USER_MODEL), urls, wsgi, asgi
│   │   ├── accounts/               # User(AbstractUser): email/is_premium/tier
│   │   │   ├── models.py          # User model, its own migrations
│   │   │   ├── admin.py           # UserAdmin exposing tier/is_premium
│   │   │   └── api/               # register/login/refresh views (is_staff/tier JWT claims), serializers, urls
│   │   ├── Dockerfile              # this service's image
│   │   ├── docker-compose.yml      # auth-db + auth-service — runs standalone
│   │   ├── requirements.txt, manage.py, .env.example
│   │   └── ...
│   ├── url-service/
│   │   ├── Config/                # settings, urls, wsgi, asgi, celery.py (Celery app + Beat schedule)
│   │   ├── url_shortener/
│   │   │   ├── models.py          # Url (owner_id/owner_email — no cross-service FK; custom_alias, tags, expiry, click_count, is_archived/archived_at), Tag
│   │   │   ├── caching.py         # cache_key/cache_url/invalidate_cache — shared by api/views.py and tasks.py
│   │   │   ├── tasks.py           # archive_expired_urls (Celery Beat) + record_click_task/delete_click_events_task/fetch_url_preview_task (queued, retried click/delete/preview reporting)
│   │   │   ├── health.py          # GET /health/ — database + Redis connectivity
│   │   │   ├── logging_utils.py   # JSONFormatter for structured stdout logging
│   │   │   ├── security/authentication.py  # StatelessJWTAuthentication (reads is_staff/tier claims) + its Swagger "Authorize" scheme
│   │   │   ├── clients/resilience.py        # CircuitBreaker + build_retrying_session — shared by every client below
│   │   │   ├── clients/analytics_client.py  # resilient click reporting + ip-api.com geolocation + cascade-delete
│   │   │   ├── clients/preview_client.py    # resilient call to preview-service for a destination page's title/description/favicon
│   │   │   └── api/               # views (short-code/alias gen, Redis cache, redirect+click_count), serializers, permissions (IsOwnerOrReadOnly), throttling (TieredUserRateThrottle), pagination (UrlPagination), urls
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml      # url-db + redis + url-service + celery-worker + celery-beat — runs standalone
│   │   └── requirements.txt, manage.py, .env.example
│   ├── analytics-service/
│   │   ├── Config/                # settings, urls, wsgi, asgi, celery.py (Celery app)
│   │   ├── analytics/
│   │   │   ├── models.py          # ClickEvent (city/country, short_code sized for a custom_alias)
│   │   │   ├── tasks.py           # track_click_task — write-behind ClickEvent persistence
│   │   │   ├── health.py          # GET /health/ — database + Redis connectivity
│   │   │   ├── logging_utils.py   # JSONFormatter for structured stdout logging
│   │   │   ├── authentication.py  # StatelessJWTAuthentication + its Swagger "Authorize" scheme
│   │   │   └── api/                # click-record/cascade-delete + stats + detailed-analytics views, permissions (IsInternalService, IsPremiumOrAdmin)
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml      # analytics-db + redis + analytics-service + celery-worker — runs standalone
│   │   └── requirements.txt, manage.py, .env.example
│   └── preview-service/             # stateless — no models, no Celery, no Postgres/Redis of its own
│       ├── Config/                 # settings (SQLite), urls, wsgi, asgi — no celery.py
│       ├── preview/
│       │   ├── fetcher.py          # fetch_preview — retrying session + per-domain circuit breaker around the arbitrary destination fetch
│       │   ├── permissions.py      # IsInternalService — same contract as analytics-service's
│       │   ├── health.py           # GET /health/ — database connectivity only (no Redis)
│       │   ├── logging_utils.py    # JSONFormatter for structured stdout logging
│       │   └── views.py            # PreviewView — POST /api/v1/preview/, internal-only
│       ├── Dockerfile
│       ├── docker-compose.yml      # single container, no db/redis — runs standalone
│       └── requirements.txt, manage.py, .env.example
├── gateway/                         # optional nginx API gateway — see API Gateway section
│   ├── server.conf                  # routing, auth_request delegation, rate limiting, timeouts (mounted as default.conf.template)
│   ├── docker-compose.yml           # single nginx container — runs standalone, joins url_shortener_gateway
│   └── .env.example                 # INTERNAL_SERVICE_TOKEN, shared with auth-service
└── README.md
```

There's deliberately no root-level `Dockerfile` or top-level orchestration
file spanning all of `services/` — each service is entirely self-contained
under its own `services/<name>/` directory. `gateway/` is the one addition
that spans them, and it's still optional and independently started.

## 🎯 API Endpoints

| Service   | Method | Endpoint                               | Auth                                 | Description                                                 |
|-----------|--------|----------------------------------------|--------------------------------------|-------------------------------------------------------------|
| auth      | POST   | `/api/v1/auth/register/`               | No                                   | Register, returns JWT tokens                                |
| auth      | POST   | `/api/v1/auth/login/`                  | No                                   | Log in, returns JWT tokens (5/min throttle)                 |
| auth      | POST   | `/api/v1/auth/refresh/`                | No                                   | Exchange refresh token for new access token                 |
| url       | POST   | `/api/v1/urls/`                        | Yes                                  | Create a new short URL (Free: capped at 10 active)          |
| url       | GET    | `/api/v1/urls/`                        | Yes                                  | List your own URLs, paginated + ?tag= (all URLs for admins) |
| url       | GET    | `/api/v1/urls/{short_code}/`           | No                                   | Retrieve full URL details (public read)                     |
| url       | PUT    | `/api/v1/urls/{short_code}/`           | Owner or admin                       | Fully update a short code                                   |
| url       | PATCH  | `/api/v1/urls/{short_code}/`           | Owner or admin                       | Partially update a short code                               |
| url       | DELETE | `/api/v1/urls/{short_code}/`           | Owner or admin                       | Delete a short code, cascading to analytics                 |
| url       | GET    | `/{short_code}/`                       | No                                   | Redirect to the original URL; reports a click event         |
| analytics | GET    | `/api/v1/analytics/urls/{short_code}/` | Yes                                  | Click count + last click time for a code you own            |
| analytics | GET    | `/api/v1/analytics/summary/`           | Yes                                  | Click counts across all short codes you own                 |
| analytics | GET    | `/api/v1/analytics/{short_code}/`      | Premium/Admin                        | Time-series + geo-location breakdown                        |
| analytics | POST   | `/api/v1/events/click/`                | Internal key                         | Called by url-service only (write-behind via Celery)        |
| analytics | DELETE | `/api/v1/events/click/`                | Internal key                         | Cascade-delete click history (called by url-service)        |
| preview   | POST   | `/api/v1/preview/`                     | Internal key                         | Fetches a destination page's title/description/favicon (called by url-service only, never through the gateway) |
| each      | GET    | `/api/schema/`, `/docs/`               | No                                   | OpenAPI schema / Swagger UI                                 |
| each      | GET    | `/admin/`                              | Session (that service's local admin) | Django admin                                                |
| url, analytics, preview | GET | `/health/`                  | No                                   | Database (+ Redis, except preview) connectivity check       |

## 🐛 Troubleshooting

### Port Already in Use
Each service's host port is set in its own `docker-compose.yml` (`8001`/`8002`/
`8003`/`8004` for the apps, `5434`/`5436`/`5435` for their databases, `6380` for
url-service's Redis, `6381` for analytics-service's Redis) — change the left
side of the `ports:` mapping for the service that conflicts. Only the
host-side number matters for this; services always talk to each other over
the internal Docker network on the container's standard port regardless of
how it's exposed to the host.

### 401s between services / tokens not verifying
`JWT_SECRET_KEY` must be **identical** across all three services' env. If you
change it, restart every service (docker-compose reads env at container start).

### Click events not showing up in analytics-service (or a preview never populates)
url-service never blocks a redirect, delete, or create on the downstream
service being reachable — the work is queued as a Celery task and retried
with backoff instead (see [Resilient HTTP Communication & Service
Decoupling](#-resilient-http-communication--service-decoupling)). Check:
- url-service's `celery-worker` container is actually running — without it,
  queued tasks just sit in Redis forever, never delivered.
- url-service's logs for `Failed to record click event` /
  `Failed to fetch preview for url=` (search `analytics_client`/
  `preview_client` in the structured JSON logs).
- `INTERNAL_API_KEY` matches across url-service, analytics-service, and
  preview-service.
- `ANALYTICS_SERVICE_URL`/`PREVIEW_SERVICE_URL` point at the right host —
  inside docker-compose that's each service's alias on the shared
  `url_shortener_gateway` network (`http://analytics:8000`,
  `http://preview:8000` — **not** `http://analytics-service:8000` /
  `http://preview-service:8000`, which are only resolvable from inside that
  *other* service's own compose project, not from url-service's containers).
  Confirm with `docker exec url_service_celery_worker python -c "import
  socket; print(socket.gethostbyname('analytics'))"` (swap in `preview` for
  the other one) — a `NameResolutionError` there means either the target
  service isn't up, or url-service's `celery-worker` isn't joined to
  `gateway-net` in its `docker-compose.yml`.

### Geo-location (city/country) always null in analytics

Two expected causes, not a bug:

1. **Local/private IPs never resolve.** `127.0.0.1`, `10.x`, `192.168.x`,
   etc. have no real-world location — `ip-api.com` correctly refuses to
   guess one. You'll only see real cities/countries when a click's
   `REMOTE_ADDR` is a genuine public IP (e.g. testing through a real deployed
   instance, not `localhost`).
2. **The lookup is best-effort and silent.** If `ip-api.com` is unreachable
   or rate-limits you, url-service logs a warning
   (`Geolocation lookup failed for ip=...`) and still reports the click with
   `city`/`country` as `null` — it never blocks or fails the click report
   over a geolocation failure.

### "Failed to redirect" / CORS error on `GET /{short_code}/`

This is expected, not a bug — and it **only** happens when the redirect is
followed by JavaScript's `fetch()` (exactly what Swagger UI's "Try it out"
does), never by a real browser tab. CORS restricts cross-origin `fetch()`/XHR
calls; it has no effect at all on a normal link click or address-bar
navigation. What actually happens: Swagger's `fetch()` follows the 302 and
then the **destination site** (whatever URL you shortened, e.g.
`example.com`) refuses the cross-origin `fetch`, which is entirely that
site's own CORS policy — url-service has no way to override a third party's
headers. The 302 response url-service sends is already correct (a clean
`Location:` header, nothing CORS-related blocking it). To see the real
behavior, open the short link directly — paste it into the browser's address
bar or click a real `<a>` link to it — never through Swagger's Execute
button.

### Migration Issues
```bash
cd services/<service-name>
python manage.py makemigrations
python manage.py migrate
```

## 📝 Development Notes

### How It Works
1. A user registers/logs in against **auth-service** and receives a JWT access + refresh token pair, with `user_id`, `email`, `is_staff`, and `tier` claims.
2. The user submits a long URL to **url-service** with `Authorization: Bearer <access-token>`. url-service verifies the token's signature itself (shared `JWT_SECRET_KEY`) and reads `user_id`/`email`/`is_staff`/`tier` straight from its claims — it never queries a Users table, because it doesn't have one.
3. url-service generates a unique short code (or validates a Premium/Admin-only `custom_alias`, and enforces the Free-tier 10-active-URL cap) and persists the `Url` row — owner, destination, alias, tags, expiry, etc. — in its own `url_db`, and caches the short_code/alias → URL/owner lookup in Redis (cache-first reads; a cache miss falls back to `url_db` and repopulates the cache; every update/delete evicts the cached entry). A Celery task (`fetch_url_preview_task`) is queued to ask **preview-service** for the destination page's title/description/favicon and fill in whichever of those three the owner didn't supply themselves — see [External Service Integration: URL Preview](#-external-service-integration-url-preview).
4. Visiting `/{short_code}/` (or a `custom_alias`) on url-service resolves the URL (cache first, then `url_db`; 404 if inactive or past `expires_at`), atomically increments `click_count`, and redirects (302) immediately. A Celery task (`record_click_task`) is queued to geolocate the IP (via a free public API) and POST a click event to **analytics-service** (`short_code`, `owner_id`, referrer, user-agent, IP, city, country) — entirely off the request/response path, so a slow/unreachable analytics-service or geolocation API never delays the redirect, and a temporary outage is retried rather than dropped (see [Resilient HTTP Communication & Service Decoupling](#-resilient-http-communication--service-decoupling)).
5. analytics-service verifies that call came from url-service via a shared `INTERNAL_API_KEY` header, validates the payload, and hands the actual write off to a Celery worker (`track_click_task.delay(...)`) — write-behind, so the view itself never blocks on a database write. Owners can query aggregate click stats for their own short codes; Premium/Admin owners can also pull a time-series + geo-location breakdown.
6. Updating, deleting, or listing a URL checks the same token's `is_staff` claim against that Url's `owner_id` — the owner or an admin may proceed, anyone else gets a 403 (reads stay public — see [Role-Based Access](#-role-based-access)); write requests are also throttled per the token's `tier` claim (see [Rate Limiting](#rate-limiting)). Deleting cascades to analytics-service's click history for that code via the same kind of queued, retried Celery task as click reporting (`delete_click_events_task`).
7. Once a day, url-service's Celery Beat scheduler fires `archive_expired_urls`: every `Url` past its `expires_at` gets `is_archived=True`, `is_active=False`, and is evicted from the cache.

### Key Design Decisions
- **Database-per-service**: `auth_db`, `url_db`, `analytics_db` are separate Postgres containers — no service can reach into another's tables. `Url.owner_id` / `ClickEvent.owner_id` are plain denormalized ids, not foreign keys, since the referenced User row lives in a different service's database entirely (see the [Database Schema](#️-database-schema) caveat about resetting auth-service's database independently of the others).
- **Stateless JWT verification**: url-service and analytics-service authenticate requests purely from the JWT's signature and claims (`url_shortener/security/authentication.py`, `analytics/authentication.py`) — no synchronous call back to auth-service on every request, and no duplicated Users table to keep in sync. Each service still keeps `django.contrib.auth` installed, but only for its own local admin-panel login, which is unrelated to this JWT-based API auth.
- **Celery-queued cross-service calls, with retries and a circuit breaker**: every *cross-service* hop from url-service (click reporting + geolocation in `RedirectUrlView`, cascade-delete in `UrlDetailView.delete`, preview fetch in `UrlListCreateView.post`) is queued as a Celery task (`record_click_task`/`delete_click_events_task`/`fetch_url_preview_task` in `url_shortener/tasks.py`) rather than called synchronously — a durable unit of work on url-service's own Redis broker, decoupled from the downstream service's availability. Each client's HTTP session (`resilience.build_retrying_session`) retries a connection failure or 5xx with exponential backoff, and its circuit breaker (`resilience.CircuitBreaker`) fails fast after 5 consecutive failures instead of piling up doomed requests; if the whole attempt still fails, Celery retries the task itself with backoff (up to 5 times) — see [Resilient HTTP Communication & Service Decoupling](#-resilient-http-communication--service-decoupling). Once a call to analytics-service lands, its own database write is a separate write-behind step: `RecordClickView` validates the payload and hands it to `track_click_task.delay(...)`, a Celery task backed by its own Redis broker, so a slow/unreachable database never blocks *that* response either. url-service uses the same Celery/Redis infrastructure for one more, unrelated purpose — `archive_expired_urls`, a Celery Beat job that runs once a day.
- **A minimal, stateless service for an inherently unreliable dependency**: fetching an arbitrary third-party page (for the URL preview feature) is the one thing in this platform that talks to hosts nobody controls, so it's isolated in its own service (preview-service) rather than done inline in url-service — a slow, malicious, or malformed response from someone else's website can only ever affect that one call, gated by its own timeout, retry, and circuit breaker, never url-service's own request handling. preview-service itself owns no models and needs no Postgres/Redis/Celery — SQLite is enough for the Django admin/auth tables it's stuck with by default.
- **Free geolocation, no fabricated data**: `ip-api.com` (no API key) is queried for city/country on each click; it correctly can't resolve private/local IPs (e.g. `127.0.0.1` in local dev), so those fields stay `null` rather than showing made-up locations.
- **Role-based access via a JWT claim, not a lookup**: url-service enforces owner-or-admin checks (`url_shortener/api/permissions.py`'s `IsOwnerOrReadOnly`) purely from the `is_staff` claim already on the token — same stateless approach as authentication itself, no call back to auth-service to check a role.
- **Tiered rate limiting via the same claim approach**: `TieredUserRateThrottle` (`url_shortener/api/throttling.py`) picks a request quota from the token's `tier` claim alone, with no lookup either.
- **Structured JSON logging**: every service logs JSON lines to stdout (`logging_utils.JSONFormatter`), with `django.request` (500s) and `django.security` (security warnings) always routed there, plus app-level `logger.warning(...)` calls at points that matter for security monitoring — a rejected `X-Internal-Key` (`analytics/api/permissions.py`, `preview/permissions.py`), an unauthorized write attempt on someone else's URL (`url_shortener/api/permissions.py`).
- **Health checks are real, not a static ping**: `GET /health/` actually queries the database (`SELECT 1`) — and, on url-service/analytics-service, pings Redis too — returning 503 (not 200) the moment either is unreachable — suitable for a container orchestrator's liveness/readiness probe.
- **RESTful Design**: proper HTTP methods and status codes, one Swagger UI per service.

## 🚢 Production Deployment

For production deployment:

1. Update each service's own `.env` with production values:
   - Set `DEBUG=False`
   - Generate strong, random values for `JWT_SECRET_KEY` and `SECRET_KEY` in every service, and `INTERNAL_API_KEY` in url-service/analytics-service/preview-service — keep the shared ones (`JWT_SECRET_KEY` across auth/url/analytics, `INTERNAL_API_KEY` across url/analytics/preview) identical across the services that share them
   - Configure `ALLOWED_HOSTS` per environment
   - Set `CORS_ALLOW_ALL_ORIGINS=False` and list real origins in `CORS_ALLOWED_ORIGINS` on every service a frontend calls (auth/url/analytics) — see [CORS for a Frontend](#-api-gateway)

2. Each service is served via Gunicorn behind its own reverse-proxy route — or behind the API gateway (`gateway/`, see [API Gateway](#-api-gateway)) for a single client-facing entry point with centralized auth and rate limiting. preview-service is never exposed publicly either way — it's reachable only from url-service, on the internal `url_shortener_gateway` network

3. url-service and analytics-service each need their Celery worker running continuously (`celery -A Config worker -l info`) for click/preview tracking and archiving to actually happen — `docker-compose.yml`'s `celery-worker` service covers this; url-service also needs `celery-beat` (`celery -A Config beat -l info`) for the nightly archive job to fire at all. preview-service needs no worker of its own — it has no Celery tasks, only a plain synchronous endpoint

4. Point your container orchestrator's liveness/readiness probes at each service's `GET /health/` — it fails (503) the moment that service's database (or, on url-service/analytics-service, Redis) is unreachable

5. Ensure the `auth_postgres_data`, `url_postgres_data`, `analytics_postgres_data`, `redis_data`, and `analytics_redis_data` volumes are backed up appropriately — preview-service has no volume worth backing up, since it stores nothing

## 📄 License

This project is created for educational purposes as part of the Python Backend course.

## 👨‍💻 Author

Created as Lab 1: URL Shortener Microservice — split into auth/url/analytics microservices.

---

**Happy URL Shortening! 🎉**
