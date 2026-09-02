# Enterprise-Grade URL Shortener — Microservices

A URL shortener platform split into three independently deployable Django REST
Framework services. Each has its own database, its own Docker image, and its
own `docker-compose.yml` — every service builds, runs, and is started
entirely on its own; there is no root-level orchestration file tying them
together, by design.

| Service | Port | Owns | Responsibility |
|---|---|---|---|
| **auth-service** | `8004` | `auth_db` (Users) | Register, log in |
| **url-service** | `8005` | `url_db` + Redis | Create short URLs, resolve/redirect, report click events |
| **analytics-service** | `8006` | `analytics_db` | Record click events, serve click stats |

```
┌──────────────┐      register/login       ┌──────────────┐
│   client     │ ─────────────────────────▶│ auth-service │
│ (browser/    │                            │   :8004      │
│  curl/etc.)  │◀──────── user id ──────────┘──────────────┘
│              │
│              │  create / redirect        ┌──────────────┐      click event      ┌───────────────────┐
│              │ ─────────────────────────▶│ url-service  │ ────────────────────▶│ analytics-service  │
└──────────────┘   (owner_id/owner_email   │   :8005      │  (X-Internal-Key)     │      :8006         │
                    sent in the request)    └──────────────┘                       └───────────────────┘
```

## 🚀 Features

- **Plain REST APIs, no authentication**: every endpoint is open (`AllowAny`) — no JWTs, no Bearer tokens, no roles/permissions to manage
- **Register/login** (auth-service): email + password, returns the user's plain `id`/`email` — the caller carries that forward on later requests
- **URL Shortening & Redirect** (url-service): short codes backed by PostgreSQL, cached in Redis for fast lookups; the caller supplies `owner_id`/`owner_email` directly in the request body
- **Click Analytics** (analytics-service): every redirect through url-service is reported as a click event; stats endpoints are scoped by an `owner_id` query parameter the caller supplies
- **Database-per-service**: each service has its own Postgres container/database — no service can query another's tables
- **API Documentation**: each service serves its own interactive Swagger UI
- **Docker Support**: every service has its own Dockerfile/image and its own `docker-compose.yml`, and is started standalone — `cd services/<name> && docker compose up --build`

## 🛠️ Technology Stack

- **Framework**: Django 5.0 + Django REST Framework, in all three services
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
its own `docker-compose.yml`, and its own `.env`/`.env.example`. Every
service is started on its own, in its own terminal.

`docker-compose.yml` (per service) reads that service's config straight from
its `env_file:` and overrides only the handful of values that must differ
between "running locally" and "running in the docker network" —
`POSTGRES_HOST`/`POSTGRES_PORT`, and (url-service only)
`REDIS_URL`/`ANALYTICS_SERVICE_URL`.

> All three services default to the same host ports for their app (`8004`/
> `8005`/`8006`) whether started via Docker or `manage.py runserver`, and
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
   `INTERNAL_API_KEY` must be identical between url-service and
   analytics-service. The `.env.example` files already ship with matching
   placeholder values — change them together if you change them at all.

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
   - auth-service: http://localhost:8004/docs/
   - url-service: http://localhost:8005/docs/
   - analytics-service: http://localhost:8006/docs/
   - Django admin (per service): `:8004/admin/`, `:8005/admin/`, `:8006/admin/`

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

3. **Run migrations and start the server**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser   # optional, for that service's admin
   python manage.py runserver
   ```
   Each service's `manage.py` is patched so a bare `runserver` (no address/port
   argument) binds to that service's own port on `localhost` — e.g.
   analytics-service prints `Starting development server at
   http://localhost:8006/`, not Django's usual `127.0.0.1:8000` default. Pass
   an explicit port (`python manage.py runserver 9000`) to override it.

## 📚 API Usage

None of these endpoints require authentication — there's no login state to
carry between requests. Instead, the caller passes whichever id it already
has (the `id` from register/login, as `owner_id`/`owner_email`) directly in
the request body or query string of the calls that need it.

### auth-service (`:8004`)

#### 1. Register — `POST /api/auth/register/`
```json
{
  "email": "alice@example.com",
  "password": "StrongPassword123",
  "confirm_password": "StrongPassword123"
}
```
**Response** (201): `{ "id": 1, "email": "alice@example.com" }`

#### 2. Login — `POST /api/auth/login/`
```json
{ "email": "alice@example.com", "password": "StrongPassword123" }
```
**Response** (200): same shape as register.

### url-service (`:8005`)

#### 3. Create Short URL — `POST /api/urls/`
```json
{
  "original_url": "https://www.example.com",
  "owner_id": 1,
  "owner_email": "alice@example.com"
}
```
**Response** (201):
```json
{
  "id": 1,
  "original_url": "https://www.example.com",
  "short_url": "abc123",
  "short_link": "http://localhost:8005/abc123/",
  "owner": "alice@example.com",
  "created_at": "2026-08-31T14:00:00Z"
}
```

#### 4. Look Up the Original URL (no redirect) — `GET /api/urls/{short_code}/`
**Response** (200): `{ "short_url": "abc123", "original_url": "https://www.example.com" }`

#### 5. Redirect — `GET /{short_code}/`
Paste directly into a browser: http://localhost:8005/abc123/ → 302 to the original URL.
Every successful redirect also reports a click event to analytics-service.

### analytics-service (`:8006`)

#### 6. Click Stats for One Short Code — `GET /api/analytics/urls/{short_code}/?owner_id=1`
**Response** (200): `{ "short_code": "abc123", "click_count": 4, "last_clicked_at": "2026-08-31T14:05:00Z" }`
Only counts clicks recorded under the given `owner_id`.

#### 7. Click Summary for an Owner — `GET /api/analytics/summary/?owner_id=1`
**Response** (200): `[ { "short_code": "abc123", "click_count": 4 }, { "short_code": "xyz789", "click_count": 1 } ]`

#### 8. Record Click (internal) — `POST /api/events/click/`
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
│   │   ├── accounts/api/          # register/login views, serializers, urls
│   │   ├── Dockerfile              # this service's image
│   │   ├── docker-compose.yml      # auth-db + auth-service — runs standalone
│   │   ├── requirements.txt, manage.py, .env.example
│   │   └── ...
│   ├── url-service/
│   │   ├── Config/
│   │   ├── url_shortener/
│   │   │   ├── models.py          # Url (owner_id/owner_email — no cross-service FK)
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
| auth | POST | `/api/auth/register/` | No | Register, returns `{id, email}` |
| auth | POST | `/api/auth/login/` | No | Log in, returns `{id, email}` |
| url | POST | `/api/urls/` | No | Create a new short URL (owner_id/owner_email in body) |
| url | GET | `/api/urls/{short_code}/` | No | Return the original URL as JSON (no redirect) |
| url | GET | `/{short_code}/` | No | Redirect to the original URL; reports a click event |
| analytics | GET | `/api/analytics/urls/{short_code}/` | No | Click count + last click time (owner_id query param) |
| analytics | GET | `/api/analytics/summary/` | No | Click counts across all short codes for owner_id |
| analytics | POST | `/api/events/click/` | Internal key | Called by url-service only |
| each | GET | `/api/schema/`, `/docs/` | No | OpenAPI schema / Swagger UI |
| each | GET | `/admin/` | Session (that service's local admin) | Django admin |

## 🐛 Troubleshooting

### Port Already in Use
Each service's host port is set in its own `docker-compose.yml` (`8004`/`8005`/
`8006` for the apps, `5434`/`5436`/`5435` for their databases, `6380` for
Redis) — change the left side of the `ports:` mapping for the service that
conflicts. Only the host-side number matters for this; services always talk
to each other over the internal Docker network on the container's standard port regardless of
how it's exposed to the host.

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
1. A user registers/logs in against **auth-service** and gets back their plain `id`/`email` — no token, no session to carry forward.
2. The user submits a long URL to **url-service** along with `owner_id`/`owner_email` in the request body. url-service doesn't verify these against anything — it trusts the caller and just stores them.
3. url-service generates a unique short code and persists `(owner_id, owner_email, original_url, short_code)` in its own `url_db`, and caches the short_code → URL/owner lookup in Redis.
4. Visiting `/{short_code}/` on url-service resolves the URL (cache first, then `url_db`) and redirects (302). Before redirecting, it POSTs a click event to **analytics-service** (`short_code`, `owner_id`, referrer, user-agent, IP) — fire-and-forget, with a short timeout, never blocking the redirect.
5. analytics-service verifies that call came from url-service via a shared `INTERNAL_API_KEY` header and persists it in its own `analytics_db`. Click stats are later queried by passing `owner_id` as a query parameter — again, trusted as given, not verified.

### Key Design Decisions
- **Database-per-service**: `auth_db`, `url_db`, `analytics_db` are separate Postgres containers — no service can reach into another's tables. `Url.owner_id` / `ClickEvent.owner_id` are plain denormalized ids, not foreign keys, since the referenced User row lives in a different service's database entirely.
- **No cross-service auth**: url-service and analytics-service accept `owner_id`/`owner_email` as plain request data instead of verifying an identity token — simpler, at the cost of trusting whatever the caller sends. Each service still keeps `django.contrib.auth` installed, but only for its own local admin-panel login, which is unrelated to the public API.
- **Fire-and-forget click events**: a redirect must succeed even if analytics-service is down, slow, or unreachable; the POST uses a 1-second timeout and swallows failures (logged, not raised).
- **RESTful Design**: proper HTTP methods and status codes, one Swagger UI per service.

## 🚢 Production Deployment

For production deployment:

1. Update each service's own `.env` with production values:
   - Set `DEBUG=False`
   - Generate strong, random values for `SECRET_KEY` in every service, and `INTERNAL_API_KEY` in url-service/analytics-service — keep `INTERNAL_API_KEY` identical across the two services that share it
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
