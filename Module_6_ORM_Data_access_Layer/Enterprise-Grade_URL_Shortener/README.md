# Enterprise-Grade URL Shortener — Microservices

A URL shortener platform split into three independently deployable Django REST
Framework services. Each has its own database, its own Docker image, and its
own `docker-compose.yml` — every service builds, runs, and is started
entirely on its own; there is no root-level orchestration file tying them
together, by design.

| Service | Port | Owns | Responsibility |
|---|---|---|---|
| **auth-service** | `8007` | `auth_db` (Users) | Register, log in, issue/refresh JWTs |
| **url-service** | `8008` | `url_db` + Redis | Create short URLs, resolve/redirect, report click events |
| **analytics-service** | `8009` | `analytics_db` | Record click events, serve click stats |

```
┌──────────────┐      register/login       ┌──────────────┐
│   client     │ ─────────────────────────▶│ auth-service │
│ (browser/    │                            │   :8007      │
│  curl/etc.)  │◀──────── JWT ──────────────┘──────────────┘
│              │
│              │  Bearer JWT               ┌──────────────┐      click event      ┌───────────────────┐
│              │ ─────────────────────────▶│ url-service  │ ────────────────────▶│ analytics-service  │
└──────────────┘   create / redirect       │   :8008      │  (X-Internal-Key)     │      :8009         │
                                            └──────────────┘                       └───────────────────┘
```

## 🚀 Features

- **JWT Authentication** (auth-service): register/login with email + password; access & refresh tokens carry a custom `email` claim
- **Stateless cross-service auth**: url-service and analytics-service verify JWTs using a secret shared with auth-service — no network call back to auth-service, no local Users table, no coupling
- **URL Shortening & Redirect** (url-service): short codes backed by PostgreSQL, cached in Redis for fast lookups
- **Click Analytics** (analytics-service): every redirect through url-service is reported as a click event; owners can query per-link and per-account click stats
- **Database-per-service**: each service has its own Postgres container/database — no service can query another's tables
- **API Documentation**: each service serves its own interactive Swagger UI
- **Docker Support**: every service has its own Dockerfile/image and its own `docker-compose.yml`, and is started standalone — `cd services/<name> && docker compose up --build`

## 🛠️ Technology Stack

- **Framework**: Django 5.0 + Django REST Framework, in all three services
- **Authentication**: JWT via `djangorestframework-simplejwt` (issued by auth-service, verified statelessly elsewhere)
- **Database**: PostgreSQL — a separate container per service
- **Cache**: Redis (`django-redis`), used by url-service only
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

`docker-compose.yml` (per service) reads that service's config straight from
its `env_file:` and overrides only the handful of values that must differ
between "running locally" and "running in the docker network" —
`POSTGRES_HOST`/`POSTGRES_PORT`, and (url-service only)
`REDIS_URL`/`ANALYTICS_SERVICE_URL`.

> All three services default to the same host ports for their app (`8007`/
> `8008`/`8009`) whether started via Docker or `manage.py runserver`, and
> whether run via their own `docker-compose.yml` or locally — so don't run the
> same service both ways at once, but the three *different* services (auth,
> url, analytics) are meant to all be running at the same time, each on its
> own port, for the platform to actually work end to end.

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
   if you change them at all.

2. **Build and start each service, in its own terminal**
   ```bash
   cd services/auth-service && docker compose up --build
   cd services/url-service && docker compose up --build
   cd services/analytics-service && docker compose up --build
   ```
   Each command also starts that service's own Postgres (and Redis, for
   url-service), so each is fully self-contained. url-service still works
   fine if analytics-service isn't running yet — it just can't reach it to
   report clicks, and logs a warning each time instead of failing the
   redirect (see `clients/analytics_client.py`).

3. **Access each service**
   - auth-service: http://localhost:8007/docs/
   - url-service: http://localhost:8008/docs/
   - analytics-service: http://localhost:8009/docs/
   - Django admin (per service): `:8007/admin/`, `:8008/admin/`, `:8009/admin/`

### Option 2: Run a Service Locally (Without Docker)

Each service under `services/` is a self-contained Django project, using the
same `.env` file from Option 1 above — no changes needed to switch between
running it in Docker and running it locally, since the values that differ
(`POSTGRES_HOST`, `POSTGRES_PORT`, etc.) are only overridden by
`docker-compose.yml`, never baked into the `.env` file itself.

1. **Create a virtual environment per service** (dependencies differ slightly
   per service, so don't share one venv across them)
   ```bash
   cd services/auth-service   # or url-service / analytics-service
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Start that service's own database** (and Redis, for url-service) — using
   that service's own `docker-compose.yml` is easiest, since it starts just
   the infra without also starting the Django app in a container:
   ```bash
   docker compose up -d auth-db                # from services/auth-service/
   docker compose up -d url-db redis            # from services/url-service/
   docker compose up -d analytics-db            # from services/analytics-service/
   ```
   Each db container is exposed on the host — `auth-db` on `5434`, `url-db` on
   `5436`, `analytics-db` on `5435`, Redis on `6380` — matching the
   `POSTGRES_PORT`/`REDIS_URL` already set in that service's `.env`.

3. **Run migrations and start the server on its own port**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser   # optional, for that service's admin
   python manage.py runserver 8007    # auth-service: 8007, url-service: 8008, analytics-service: 8009
   ```
   `runserver` defaults to port `8000` if you omit the port argument — always
   pass it explicitly, or all three services will try to bind the same port.

## 🔑 Authenticating Requests

Every protected endpoint expects the access token as a **Bearer token** on the
`Authorization` header — that's the one and only place it goes:

```text
Authorization: Bearer <your-access-token>
```

**In Swagger UI** (`:8007/docs/`, `:8008/docs/`, `:8009/docs/`):

1. Register or log in via auth-service's `/api/auth/register/` or `/api/auth/login/` and copy the `access` value from the response.
2. On whichever service's Swagger page you want to call, click the green **Authorize** button (top right), paste just the raw token — no `Bearer` prefix, Swagger adds that — and click **Authorize**.
3. Every "Try it out" call on that page now sends it automatically.

**Via curl / any HTTP client**, set the header directly:
```bash
curl -X POST http://localhost:8008/api/urls/ \
  -H "Authorization: Bearer <your-access-token>" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com"}'
```

The token is only ever issued by auth-service, but url-service and
analytics-service both verify it themselves (see `authentication.py` in each)
and both show the same Authorize button — this required manually registering
a `drf_spectacular.extensions.OpenApiAuthenticationExtension` for
`StatelessJWTAuthentication`, since drf-spectacular only auto-detects the
stock `JWTAuthentication` class, not a subclass of it.

## 📚 API Usage

### auth-service (`:8007`)

#### 1. Register — `POST /api/auth/register/`
```json
{
  "email": "alice@example.com",
  "password": "StrongPassword123",
  "confirm_password": "StrongPassword123"
}
```
**Response** (201): `{ "id": 1, "email": "alice@example.com", "access": "...", "refresh": "..." }`

#### 2. Login — `POST /api/auth/login/`
```json
{ "email": "alice@example.com", "password": "StrongPassword123" }
```
**Response** (200): same shape as register.

#### 3. Refresh — `POST /api/auth/refresh/`
```json
{ "refresh": "<jwt-refresh-token>" }
```
**Response** (200): `{ "access": "<new-jwt-access-token>" }`

### url-service (`:8008`)

#### 4. Create Short URL — `POST /api/urls/` (requires `Authorization: Bearer <access-token>`)
```json
{ "original_url": "https://www.example.com" }
```
**Response** (201):
```json
{
  "id": 1,
  "original_url": "https://www.example.com",
  "short_url": "abc123",
  "short_link": "http://localhost:8008/abc123/",
  "owner": "alice@example.com",
  "created_at": "2026-08-31T14:00:00Z"
}
```

#### 5. Look Up the Original URL (no redirect) — `GET /api/urls/{short_code}/`
**Response** (200): `{ "short_url": "abc123", "original_url": "https://www.example.com" }`

#### 6. Redirect — `GET /{short_code}/`
Paste directly into a browser: http://localhost:8008/abc123/ → 302 to the original URL.
Every successful redirect also reports a click event to analytics-service.

### analytics-service (`:8009`, requires `Authorization: Bearer <access-token>`)

#### 7. Click Stats for One Short Code — `GET /api/analytics/urls/{short_code}/`
**Response** (200): `{ "short_code": "abc123", "click_count": 4, "last_clicked_at": "2026-08-31T14:05:00Z" }`
Only counts clicks recorded under your own user id.

#### 8. Your Click Summary — `GET /api/analytics/summary/`
**Response** (200): `[ { "short_code": "abc123", "click_count": 4 }, { "short_code": "xyz789", "click_count": 1 } ]`

#### 9. Record Click (internal) — `POST /api/events/click/`
Called by url-service on every redirect, not meant for direct/public use — requires
the `X-Internal-Key` header to match `INTERNAL_API_KEY`.

## 🧪 Testing

Each service has its own test suite:
```bash
cd services/auth-service && python manage.py test
cd services/url-service && python manage.py test
cd services/analytics-service && python manage.py test
```

## 📁 Project Structure

```
Enterprise-Grade_URL_Shortener/
├── services/
│   ├── auth-service/
│   │   ├── Config/                # settings, urls, wsgi, asgi
│   │   ├── accounts/api/          # register/login/refresh views, serializers, urls
│   │   ├── Dockerfile              # this service's image
│   │   ├── docker-compose.yml      # auth-db + auth-service — runs standalone
│   │   ├── requirements.txt, manage.py, .env.example
│   │   └── ...
│   ├── url-service/
│   │   ├── Config/
│   │   ├── url_shortener/
│   │   │   ├── models.py          # Url (owner_id/owner_email — no cross-service FK)
│   │   │   ├── authentication.py  # StatelessJWTAuthentication + its Swagger "Authorize" scheme
│   │   │   ├── clients/analytics_client.py  # fire-and-forget click reporting
│   │   │   ├── domain/, services/ # short-code gen, repository, Redis cache, orchestration
│   │   │   └── api/               # views, serializers, urls
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml      # url-db + redis + url-service — runs standalone
│   │   └── requirements.txt, manage.py, .env.example
│   └── analytics-service/
│       ├── Config/
│       ├── analytics/
│       │   ├── models.py          # ClickEvent
│       │   ├── authentication.py  # StatelessJWTAuthentication + its Swagger "Authorize" scheme
│       │   └── api/                # click-record + stats views, permissions.IsInternalService
│       ├── Dockerfile
│       ├── docker-compose.yml      # analytics-db + analytics-service — runs standalone
│       └── requirements.txt, manage.py, .env.example
└── README.md
```

There's deliberately no root-level `Dockerfile`, `docker-compose.yml`, or `.env`
— nothing at this level ties the services together; each is entirely
self-contained under its own `services/<name>/` directory.

## 🎯 API Endpoints

| Service | Method | Endpoint | Auth | Description |
|---|---|---|---|---|
| auth | POST | `/api/auth/register/` | No | Register, returns JWT tokens |
| auth | POST | `/api/auth/login/` | No | Log in, returns JWT tokens |
| auth | POST | `/api/auth/refresh/` | No | Exchange refresh token for new access token |
| url | POST | `/api/urls/` | Yes | Create a new short URL |
| url | GET | `/api/urls/{short_code}/` | No | Return the original URL as JSON (no redirect) |
| url | GET | `/{short_code}/` | No | Redirect to the original URL; reports a click event |
| analytics | GET | `/api/analytics/urls/{short_code}/` | Yes | Click count + last click time for a code you own |
| analytics | GET | `/api/analytics/summary/` | Yes | Click counts across all short codes you own |
| analytics | POST | `/api/events/click/` | Internal key | Called by url-service only |
| each | GET | `/api/schema/`, `/docs/` | No | OpenAPI schema / Swagger UI |
| each | GET | `/admin/` | Session (that service's local admin) | Django admin |

## 🐛 Troubleshooting

### Port Already in Use
Each service's host port is set in its own `docker-compose.yml` (`8007`/`8008`/
`8009` for the apps, `5434`/`5436`/`5435` for their databases, `6380` for
Redis) — change the left side of the `ports:` mapping for the service that
conflicts. Only the host-side number matters for this; services always talk
to each other over the internal Docker network on the container's standard port regardless of
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

### Migration Issues
```bash
cd services/<service-name>
python manage.py makemigrations
python manage.py migrate
```

## 📝 Development Notes

### How It Works
1. A user registers/logs in against **auth-service** and receives a JWT access + refresh token pair, with `user_id` and `email` claims.
2. The user submits a long URL to **url-service** with `Authorization: Bearer <access-token>`. url-service verifies the token's signature itself (shared `JWT_SECRET_KEY`) and reads `user_id`/`email` straight from its claims — it never queries a Users table, because it doesn't have one.
3. url-service generates a unique short code and persists `(owner_id, owner_email, original_url, short_code)` in its own `url_db`, and caches the short_code → URL/owner lookup in Redis.
4. Visiting `/{short_code}/` on url-service resolves the URL (cache first, then `url_db`) and redirects (302). Before redirecting, it POSTs a click event to **analytics-service** (`short_code`, `owner_id`, referrer, user-agent, IP) — fire-and-forget, with a short timeout, never blocking the redirect.
5. analytics-service verifies that call came from url-service via a shared `INTERNAL_API_KEY` header and persists it in its own `analytics_db`. Owners can later query aggregate click stats for their own short codes.

### Key Design Decisions
- **Database-per-service**: `auth_db`, `url_db`, `analytics_db` are separate Postgres containers — no service can reach into another's tables. `Url.owner_id` / `ClickEvent.owner_id` are plain denormalized ids, not foreign keys, since the referenced User row lives in a different service's database entirely.
- **Stateless JWT verification**: url-service and analytics-service authenticate requests purely from the JWT's signature and claims (`url_shortener/authentication.py`, `analytics/authentication.py`) — no synchronous call back to auth-service on every request, and no duplicated Users table to keep in sync. Each service still keeps `django.contrib.auth` installed, but only for its own local admin-panel login, which is unrelated to this JWT-based API auth.
- **Fire-and-forget click events**: a redirect must succeed even if analytics-service is down, slow, or unreachable; the POST uses a 1-second timeout and swallows failures (logged, not raised).
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
