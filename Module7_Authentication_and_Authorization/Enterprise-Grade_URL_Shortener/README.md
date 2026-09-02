# Enterprise-Grade URL Shortener — Microservices

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-REST%20Framework-A30000)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-Educational-lightgrey)

A URL shortener platform split into three independently deployable Django REST
Framework services. Each has its own database and its own Docker image; all
three, plus a single shared Postgres instance and Redis, are brought up
together by one root-level `docker-compose.yml`.

| Service               | Port   | Owns                       | Responsibility                                           |
|-----------------------|--------|----------------------------|----------------------------------------------------------|
| **auth-service**      | `8001` | `auth_service` db (Users)  | Register, log in, issue/refresh JWTs                     |
| **url-service**       | `8002` | `url_service` db + Redis   | Create short URLs, resolve/redirect, report click events |
| **analytics-service** | `8003` | `analytics_service` db     | Record click events, serve click stats                   |

All three databases live in one shared Postgres container (`localhost:5432`,
user `postgres` / password `patrick`) — each service still only ever touches
its own database, it's just one Postgres instance hosting all three instead
of one container per service.

```
┌──────────────┐      register/login       ┌──────────────┐
│   client     │ ─────────────────────────▶│ auth-service │
│ (browser/    │                            │   :8001      │
│  curl/etc.)  │◀──────── JWT ──────────────┘──────────────┘
│              │
│              │  Bearer JWT               ┌──────────────┐      click event      ┌───────────────────┐
│              │ ─────────────────────────▶│ url-service  │ ────────────────────▶│ analytics-service  │
└──────────────┘   create / redirect       │   :8002      │  (X-Internal-Key)     │      :8003         │
                                            └──────────────┘                       └───────────────────┘
```

## 📑 Table of Contents

- [Features](#-features)
- [Technology Stack](#️-technology-stack)
- [Prerequisites](#-prerequisites)
- [Setup Instructions](#-setup-instructions)
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
- **URL Shortening & Redirect** (url-service): short codes (or a Premium custom alias) backed by PostgreSQL, cached in Redis for fast lookups; supports tags, expiry, activation toggling, and per-link metadata
- **Click Analytics** (analytics-service): every redirect through url-service is reported as a click event; owners can query per-link and per-account click stats
- **Database-per-service**: each service has its own Postgres database (all three hosted in one shared container) — no service can query another's tables
- **API Documentation**: each service serves its own interactive Swagger UI
- **Docker Support**: every service has its own Dockerfile/image; a single root-level `docker-compose.yml` builds and starts all three together, alongside the shared Postgres and Redis — `docker compose up --build`

## 🛠️ Technology Stack

- **Framework**: Django 5.0 + Django REST Framework, in all three services
- **Authentication**: JWT via `djangorestframework-simplejwt` (issued by auth-service, verified statelessly elsewhere)
- **Database**: PostgreSQL — one shared container, a separate database per service
- **Cache**: Redis (`django-redis`), used by url-service only
- **API Documentation**: drf-spectacular (OpenAPI/Swagger) per service
- **Server**: Gunicorn (production)
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized setup, or to run Postgres/Redis locally)

## 🔧 Setup Instructions

There's no root-level `.env` — each service under `services/` still keeps its
own `Dockerfile` and its own `.env`/`.env.example` (secrets included).
Orchestration, though, is one level up: a single root-level
`docker-compose.yml` builds and starts all three services together, plus one
shared Postgres container (all three databases side by side) and Redis.

The root `docker-compose.yml` reads each service's config straight from its
`env_file:` and overrides only the handful of values that must differ between
"running locally" and "running in the docker network" —
`POSTGRES_HOST`/`POSTGRES_PORT`, and (url-service only)
`REDIS_URL`/`ANALYTICS_SERVICE_URL`.

> Each service's app defaults to its own host port (`8001`/`8002`/`8003`)
> whether started via Docker or `manage.py runserver` — so don't run the same
> service both ways at once, but the three *different* services (auth, url,
> analytics) are meant to all be running at the same time, each on its own
> port, for the platform to actually work end to end.

### Option 1: Run with Docker (Recommended)

1. **Copy each service's env file** (only needed once — real `.env` files are
   gitignored, so if they're already present you can skip this)
   ```bash
   cp services/auth-service/.env.example services/auth-service/.env
   cp services/url-service/.env.example services/url-service/.env
   cp services/analytics-service/.env.example services/analytics-service/.env
   ```
   `JWT_SECRET_KEY` must be identical across all three; `INTERNAL_API_KEY` must
   be identical between url-service and analytics-service. The `.env.example`
   files already ship with matching placeholder values — change them together
   if you change them at all. `POSTGRES_HOST`/`POSTGRES_PORT` in each file
   (`localhost:5432`) match the shared Postgres container defined in the root
   `docker-compose.yml`, so they don't need to be touched either.

2. **Build and start everything, from the repo root**
   ```bash
   docker compose up --build
   ```
   This starts the shared Postgres container (creating `auth_service`,
   `url_service`, and `analytics_service` databases inside it on first boot —
   see `db/init-databases.sh`), Redis, and all three Django services. Postgres
   is reachable on the host at `localhost:5432` (user `postgres`, password
   `patrick`, maintenance database `postgres`) — the same credentials you'd
   use to register a server connection in pgAdmin. Data persists in the
   `shared_postgres_data` Docker volume across restarts.

3. **Access each service**
   - auth-service: http://localhost:8001/docs/
   - url-service: http://localhost:8002/docs/
   - analytics-service: http://localhost:8003/docs/
   - Django admin (per service): `:8001/admin/`, `:8002/admin/`, `:8003/admin/`

### Option 2: Run a Service Locally (Without Docker)

Each service under `services/` is a self-contained Django project, using the
same `.env` file from Option 1 above — no changes needed to switch between
running it in Docker and running it locally, since the values that differ
(`POSTGRES_HOST`, `POSTGRES_PORT`, etc.) are only overridden by the root
`docker-compose.yml`, never baked into the `.env` file itself.

1. **Create a virtual environment per service** (dependencies differ slightly
   per service, so don't share one venv across them)
   ```bash
   cd services/auth-service   # or url-service / analytics-service
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Start the shared infra** (Postgres + Redis) — from the repo root, this
   starts just the infra without also starting the Django apps in containers:
   ```bash
   docker compose up -d postgres redis
   ```
   Postgres is exposed on the host at `5432`, Redis at `6380` — matching
   `POSTGRES_PORT`/`REDIS_URL` already set in each service's `.env`.

3. **Run migrations and start the server on its own port**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser   # optional, for that service's admin
   python manage.py runserver
   ```
   With no addrport argument, `runserver` normally falls back to `8000` for
   every service — `manage.py` here instead defaults it to that service's own
   `PORT` from `.env` (`8001`/`8002`/`8003`), so running all three locally at
   once doesn't collide. Pass an addrport explicitly (e.g. `runserver 9000`)
   to override it.

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
`favicon`, `is_active`, `expires_at`, and `tags` are all optional.
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
removing that code's click history there too (fire-and-forget, in the
background — see [Role-Based Access](#-role-based-access)).
**Response** (204): empty body.

#### 10. Redirect — `GET /{short_code}/` (or a `custom_alias`)
Paste directly into a browser: http://localhost:8002/abc123/ → 302 to the
original URL. Returns 404 if inactive or expired. Every successful redirect
increments `click_count` and reports a click event (with best-effort
geolocation) to analytics-service — both happen in a background thread, so
they never delay the redirect itself.

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
`X-Internal-Key` header to match `INTERNAL_API_KEY`. `POST` records a click;
`DELETE` (body: `{"short_codes": [...]}`) cascade-deletes click history for
those codes, called when url-service deletes a URL.

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
there too — both the delete and the cascade call run synchronously in the
request/response cycle except the actual HTTP call to analytics-service,
which fires from a background thread so a slow/unreachable analytics-service
never delays the 204 response.

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
| `title`, `description`, `favicon` | `CharField(null=True)`                  | User-supplied metadata, not auto-fetched from the destination |
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
├── db/
│   └── init-databases.sh          # creates auth_service/url_service/analytics_service dbs on first boot
├── docker-compose.yml             # shared postgres + redis + all three services — the one orchestration file
├── services/
│   ├── auth-service/
│   │   ├── Config/                # settings (AUTH_USER_MODEL), urls, wsgi, asgi
│   │   ├── accounts/               # User(AbstractUser): email/is_premium/tier
│   │   │   ├── models.py          # User model, its own migrations
│   │   │   ├── admin.py           # UserAdmin exposing tier/is_premium
│   │   │   └── api/               # register/login/refresh views (is_staff/tier JWT claims), serializers, urls
│   │   ├── Dockerfile              # this service's image
│   │   ├── requirements.txt, manage.py, .env.example
│   │   └── ...
│   ├── url-service/
│   │   ├── Config/
│   │   ├── url_shortener/
│   │   │   ├── models.py          # Url (owner_id/owner_email — no cross-service FK; custom_alias, tags, expiry, click_count), Tag
│   │   │   ├── security/authentication.py  # StatelessJWTAuthentication (reads is_staff/tier claims) + its Swagger "Authorize" scheme
│   │   │   ├── clients/analytics_client.py  # fire-and-forget click reporting + ip-api.com geolocation + cascade-delete
│   │   │   └── api/               # views (short-code/alias gen, Redis cache, redirect+click_count, background threading), serializers, permissions (IsOwnerOrReadOnly), throttling (TieredUserRateThrottle), pagination (UrlPagination), urls
│   │   ├── Dockerfile
│   │   └── requirements.txt, manage.py, .env.example
│   └── analytics-service/
│       ├── Config/
│       ├── analytics/
│       │   ├── models.py          # ClickEvent (city/country, short_code sized for a custom_alias)
│       │   ├── authentication.py  # StatelessJWTAuthentication + its Swagger "Authorize" scheme
│       │   └── api/                # click-record/cascade-delete + stats + detailed-analytics views, permissions (IsInternalService, IsPremiumOrAdmin)
│       ├── Dockerfile
│       └── requirements.txt, manage.py, .env.example
└── README.md
```

Each service still keeps its own `Dockerfile` and `.env`/`.env.example`
(secrets included), but orchestration lives in the single root-level
`docker-compose.yml` — that's what ties the services, the shared Postgres
container, and Redis together.

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
| analytics | POST   | `/api/v1/events/click/`                | Internal key                         | Called by url-service only                                  |
| analytics | DELETE | `/api/v1/events/click/`                | Internal key                         | Cascade-delete click history (called by url-service)        |
| each      | GET    | `/api/schema/`, `/docs/`               | No                                   | OpenAPI schema / Swagger UI                                 |
| each      | GET    | `/admin/`                              | Session (that service's local admin) | Django admin                                                |

## 🐛 Troubleshooting

### Port Already in Use
Every host port is set in the root `docker-compose.yml` (`8001`/`8002`/`8003`
for the apps, `5432` for the shared Postgres, `6380` for Redis) — change the
left side of the `ports:` mapping for the service that conflicts. Only the
host-side number matters for this; services always talk to each other over
the internal Docker network on the container's standard port regardless of
how it's exposed to the host.

### 401s between services / tokens not verifying
`JWT_SECRET_KEY` must be **identical** across all three services' env. If you
change it, restart every service (docker-compose reads env at container start).

### Click events not showing up in analytics-service
url-service never blocks a redirect on analytics-service being reachable — it
logs a warning and moves on. Check url-service's logs for
`Failed to record click event`, and confirm `INTERNAL_API_KEY` matches between
url-service and analytics-service, and `ANALYTICS_SERVICE_URL` points at the
right host (`http://analytics-service:8000` inside docker-compose).

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
3. url-service generates a unique short code (or validates a Premium/Admin-only `custom_alias`, and enforces the Free-tier 10-active-URL cap) and persists the `Url` row — owner, destination, alias, tags, expiry, etc. — in its own `url_db`, and caches the short_code/alias → URL/owner lookup in Redis.
4. Visiting `/{short_code}/` (or a `custom_alias`) on url-service resolves the URL (cache first, then `url_db`; 404 if inactive or past `expires_at`), atomically increments `click_count`, and redirects (302) immediately. A background thread then geolocates the IP (via a free public API) and POSTs a click event to **analytics-service** (`short_code`, `owner_id`, referrer, user-agent, IP, city, country) — entirely off the request/response path, so a slow/unreachable analytics-service or geolocation API never delays the redirect.
5. analytics-service verifies that call came from url-service via a shared `INTERNAL_API_KEY` header and persists it in its own `analytics_db`. Owners can query aggregate click stats for their own short codes; Premium/Admin owners can also pull a time-series + geo-location breakdown.
6. Updating, deleting, or listing a URL checks the same token's `is_staff` claim against that Url's `owner_id` — the owner or an admin may proceed, anyone else gets a 403 (reads stay public — see [Role-Based Access](#-role-based-access)); write requests are also throttled per the token's `tier` claim (see [Rate Limiting](#rate-limiting)). Deleting cascades to analytics-service's click history for that code, via the same kind of background thread as click reporting.

### Key Design Decisions
- **Database-per-service**: `auth_db`, `url_db`, `analytics_db` are separate Postgres containers — no service can reach into another's tables. `Url.owner_id` / `ClickEvent.owner_id` are plain denormalized ids, not foreign keys, since the referenced User row lives in a different service's database entirely (see the [Database Schema](#️-database-schema) caveat about resetting auth-service's database independently of the others).
- **Stateless JWT verification**: url-service and analytics-service authenticate requests purely from the JWT's signature and claims (`url_shortener/security/authentication.py`, `analytics/authentication.py`) — no synchronous call back to auth-service on every request, and no duplicated Users table to keep in sync. Each service still keeps `django.contrib.auth` installed, but only for its own local admin-panel login, which is unrelated to this JWT-based API auth.
- **Background-thread "async" analytics**: no Celery/task-queue infrastructure exists in this project, so click reporting and geolocation (`RedirectUrlView`) and cascade-delete (`UrlDetailView.delete`) run on a plain daemon `threading.Thread` rather than blocking the response — pragmatic for this project's scale, not a durable/retryable production task queue.
- **Free geolocation, no fabricated data**: `ip-api.com` (no API key) is queried for city/country on each click; it correctly can't resolve private/local IPs (e.g. `127.0.0.1` in local dev), so those fields stay `null` rather than showing made-up locations.
- **Role-based access via a JWT claim, not a lookup**: url-service enforces owner-or-admin checks (`url_shortener/api/permissions.py`'s `IsOwnerOrReadOnly`) purely from the `is_staff` claim already on the token — same stateless approach as authentication itself, no call back to auth-service to check a role.
- **Tiered rate limiting via the same claim approach**: `TieredUserRateThrottle` (`url_shortener/api/throttling.py`) picks a request quota from the token's `tier` claim alone, with no lookup either.
- **RESTful Design**: proper HTTP methods and status codes, one Swagger UI per service.

## 🚢 Production Deployment

For production deployment:

1. Update each service's own `.env` with production values:
   - Set `DEBUG=False`
   - Generate strong, random values for `JWT_SECRET_KEY` and `SECRET_KEY` in every service, and `INTERNAL_API_KEY` in url-service/analytics-service — keep the shared ones (`JWT_SECRET_KEY` everywhere, `INTERNAL_API_KEY` on url-service + analytics-service) identical across the services that share them
   - Configure `ALLOWED_HOSTS` per environment
   - Set `CORS_ALLOW_ALL_ORIGINS=False` and list real origins in `CORS_ALLOWED_ORIGINS`

2. Each service is served via Gunicorn behind its own reverse-proxy route (or an API gateway, if you add one later)

3. Ensure the `auth_postgres_data`, `url_postgres_data`, `analytics_postgres_data`, and `redis_data` volumes are backed up appropriately

## 📄 License

This project is created for educational purposes as part of the Python Backend course.

## 👨‍💻 Author

Created as Lab 1: URL Shortener Microservice — split into auth/url/analytics microservices.

---

**Happy URL Shortening! 🎉**
