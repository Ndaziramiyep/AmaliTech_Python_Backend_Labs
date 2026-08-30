# URL Shortener Microservice

A URL shortener microservice built with Django REST Framework, featuring JWT authentication, custom user tiers, click analytics, tagging, Redis-backed caching, PostgreSQL persistence, Docker containerization, and interactive API documentation with Swagger UI.

## 🚀 Features

- **JWT Authentication**: Register and log in with email + password; every short-URL operation is scoped to the authenticated user
- **User Tiers**: Custom `User` model with `is_premium` and `tier` (Free / Premium / Admin)
- **Ownership Enforcement**: `IsOwnerOrReadOnly` blocks any user from viewing, editing, or deleting a URL they don't own
- **URL Shortening**: Convert long URLs into short, shareable links tied to their owner, with an optional custom alias, title/description/favicon metadata, and an expiry date
- **Tags**: Many-to-many tagging of URLs (e.g. Marketing, Social), seeded with defaults via a data migration
- **Click Analytics**: Every redirect logs a `Click` (IP, user agent, referrer, country, city); premium accounts get time-series and geo breakdowns
- **Automatic Redirect**: Short URLs redirect (302) to their original URL, skipping inactive or expired links
- **Redis Caching**: Fast short-code lookups cached in Redis, backed by PostgreSQL as the source of truth
- **Query Optimization**: Custom manager (`active_urls`, `expired_urls`, `popular_urls`), `select_related`/`prefetch_related` on list/detail views, and indexes on `short_code` and `created_at`
- **REST API**: Clean, versioned (`/api/v1/`) RESTful API with proper HTTP status codes
- **API Documentation**: Interactive Swagger UI for testing endpoints
- **Docker Support**: Fully containerized with Docker Compose (Postgres + Redis + web)
- **Admin Panel**: Django admin interface for managing users, URLs, clicks, and tags

## 🛠️ Technology Stack

- **Framework**: Django 5.0 + Django REST Framework
- **Authentication**: JWT via `djangorestframework-simplejwt`
- **Database**: PostgreSQL (via `psycopg` v3)
- **Cache**: Redis (`django-redis`)
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Server**: Gunicorn (production)
- **Containerization**: Docker & Docker Compose

## 🏗️ Architecture

```
                         ┌───────────────────────┐
   client / browser ───▶ │   config/urls.py       │
                         │  (routing + Swagger)   │
                         └──────────┬─────────────┘
                                    │
                 ┌──────────────────┼───────────────────┐
                 ▼                                       ▼
       url_shortener/api/                        RedirectUrlView
   (serializers, views, urls)                    (public, GET /{code}/)
                 │                                       │
                 ▼                                       ▼
      services/url_shortener_service.py  ──▶  Url.objects (URLManager)
                 │                                       │
        ┌────────┴────────┐                              ▼
        ▼                 ▼                        Click (analytics)
  domain/interfaces   RedisUrlCache
  (repository, cache,        │
   code generator)           ▼
        │                Redis (cache)
        ▼
   PostgreSQL (source of truth: User, Url, Click, Tag)
```

Layers:
- **api/** — DRF serializers + views + routing (HTTP boundary)
- **services/** — `UrlShortenerService` coordinates code generation, persistence, and caching
- **domain/interfaces.py** — abstract contracts (`ShortCodeGenerator`, `UrlRepository`, `UrlCacheBackend`) the services implement, keeping the business logic decoupled from Django/Redis specifics
- **models.py / managers.py** — the ORM layer: `User`, `Url`, `Click`, `Tag`, and the `URLManager` custom queryset

## 🗄️ Database Schema

| Model | Key fields |
|-------|-----------|
| `User` (extends `AbstractUser`) | `email` (unique), `is_premium`, `tier` (`free`/`premium`/`admin`) |
| `Url` | `original_url`, `short_code` (unique, indexed, ≤10 chars), `custom_alias` (nullable, unique), `owner` (FK → `User`, CASCADE), `tags` (M2M → `Tag`), `is_active`, `expires_at`, `title`, `description`, `favicon`, `click_count`, `created_at` (indexed) |
| `Click` | `url` (FK → `Url`, CASCADE), `clicked_at`, `ip_address`, `city`, `country`, `user_agent`, `referrer` |
| `Tag` | `name` (unique) |

### Custom manager (`Url.objects`)
- `active_urls()` — `is_active=True` and not expired
- `expired_urls()` — has an `expires_at` in the past
- `popular_urls()` — ordered by `click_count` descending
- `with_related()` — `select_related('owner')` + `prefetch_related('tags')` to avoid N+1 queries on list/detail views

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized setup, or to run Postgres/Redis locally)

## 🔧 Setup Instructions

### Option 1: Run with Docker (Recommended)

1. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

2. **Build and start containers**
   ```bash
   docker-compose up --build
   ```
   This creates the Postgres database named by `POSTGRES_DB` in `.env` (defaults to `url_shortener_06`) and runs migrations automatically before starting Gunicorn.

3. **Access the application**
   - API Documentation (Swagger): http://localhost:8000/docs/
   - Django Admin: http://localhost:8000/admin/
   - API base: http://localhost:8000/api/v1/

### Option 2: Run Locally (Without Docker)

1. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Copy `.env.example` to `.env` and fill in your values**
   ```bash
   cp .env.example .env
   ```
   Local Postgres and Redis can be started with `docker-compose up -d db redis`
   (the Postgres container is exposed on host port `5433` to avoid clashing
   with a locally installed Postgres on `5432`; see `POSTGRES_PORT` in `.env`).
   If the database named in `POSTGRES_DB` doesn't exist yet in that Postgres
   instance, create it once: `docker exec <db-container> psql -U postgres -c "CREATE DATABASE url_shortener_06;"`

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```
   This also seeds default tags (Marketing, Social, Personal, Business, Other) via a data migration.

5. **Create superuser** (optional, for admin access)
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

## 📚 API Usage

All endpoints except registration, login, token refresh, and the public redirect require a JWT access token sent as `Authorization: Bearer <access-token>`.

### Authentication

**`POST /api/v1/auth/register/`**
```json
{
  "email": "alice@example.com",
  "password": "StrongPassword123",
  "confirm_password": "StrongPassword123"
}
```
Response (201): `{ "id", "email", "tier", "access", "refresh" }`

**`POST /api/v1/auth/login/`** — same request/response shape as register, without `confirm_password`.

**`POST /api/v1/auth/refresh/`**
```json
{ "refresh": "<jwt-refresh-token>" }
```
Response (200): `{ "access": "<new-jwt-access-token>" }`

### URL Operations

**`POST /api/v1/urls/`** — create a short URL (requires auth)
```json
{
  "original_url": "https://www.example.com",
  "custom_alias": "mylink",
  "title": "Example",
  "expires_at": "2027-01-01T00:00:00Z",
  "tags": ["Marketing", "Social"]
}
```
Only `original_url` is required. Response (201) is the full `Url` representation including `short_code`, `short_link`, `tags`, `click_count`, `is_expired`, etc.

**`GET /api/v1/urls/`** — list the authenticated user's URLs (owner `select_related`, tags `prefetch_related`)

**`GET /api/v1/urls/{short_code}/`** — retrieve one of the authenticated user's URLs (404/403 if not the owner)

**`PUT /api/v1/urls/{short_code}/`** — partially update `original_url`, `title`, `description`, `favicon`, `is_active`, `expires_at`, `tags`

**`DELETE /api/v1/urls/{short_code}/`** — deactivate the URL (`is_active=False`); the redirect endpoint then 404s for it

### Public Interface

**`GET /{short_code}/`** — redirect (302) to the original URL. Skips inactive/expired URLs (404). Logs a `Click` (IP, user agent, referrer) and atomically increments `click_count` on every hit.

### Analytics (Premium only)

**`GET /api/v1/analytics/{short_code}/`** — requires an authenticated **premium** (or admin-tier) owner; returns:
```json
{
  "short_code": "mylink",
  "total_clicks": 42,
  "clicks_by_country": [{"country": "US", "count": 30}, ...],
  "clicks_by_day": [{"day": "2026-08-01", "count": 5}, ...],
  "top_referrers": [{"referrer": "https://twitter.com", "count": 10}, ...]
}
```
All three breakdowns are computed in SQL via `annotate()`/`Count()` (and `TruncDate()` for the daily series) rather than in Python.

## 🧪 Testing

```bash
python manage.py test
```

The suite covers: `User`/`Url`/`Click`/`Tag` models, the `URLManager` queryset methods, the caching service layer, auth (register/login), URL CRUD + ownership permissions, the redirect + click-logging flow, and the premium-only analytics endpoint.

## 📁 Project Structure

```
Enterprise-Grade_URL_Shortener/
├── config/                       # Django project settings
│   ├── settings.py               # Settings, loaded from environment variables (.env)
│   ├── urls.py                   # Root URL routing + Swagger endpoints
│   ├── wsgi.py                   # WSGI configuration
│   └── asgi.py                   # ASGI configuration
├── url_shortener/                # Main application
│   ├── models.py                 # User, Url, Click, Tag
│   ├── managers.py                # URLManager / URLQuerySet (active/expired/popular)
│   ├── permissions.py             # IsOwnerOrReadOnly, IsPremiumUser
│   ├── admin.py                   # Admin configuration for all models
│   ├── domain/                    # Abstract interfaces (generator, repository, cache)
│   ├── services/                  # Business logic implementing the domain interfaces
│   ├── api/                       # DRF serializers, views (auth + URLs + analytics), routing
│   ├── migrations/                # Schema + data migration (seeds default tags)
│   └── tests/                     # Test suite (models, services, auth, API)
├── manage.py                     # Django management script
├── Dockerfile                    # Docker image build
├── docker-compose.yml            # db (Postgres) + redis + web services
├── requirements.txt              # Python dependencies
├── .env / .env.example           # Environment configuration
└── README.md                     # This file
```

## 🎯 API Endpoints

| Method | Endpoint | Auth required | Description |
|--------|----------|----------------|-------------|
| POST | `/api/v1/auth/register/` | No | Register with email/password/confirm_password, returns JWT tokens |
| POST | `/api/v1/auth/login/` | No | Log in with email/password, returns JWT tokens |
| POST | `/api/v1/auth/refresh/` | No | Exchange a refresh token for a new access token |
| POST | `/api/v1/urls/` | Yes | Create a new short URL |
| GET | `/api/v1/urls/` | Yes | List the authenticated user's URLs |
| GET | `/api/v1/urls/{short_code}/` | Yes (owner) | Retrieve URL details |
| PUT | `/api/v1/urls/{short_code}/` | Yes (owner) | Update a URL |
| DELETE | `/api/v1/urls/{short_code}/` | Yes (owner) | Deactivate a URL |
| GET | `/api/v1/analytics/{short_code}/` | Yes (owner, premium) | Time-series + geo click analytics |
| GET | `/{short_code}/` | No | Redirect to the original URL, logs a click |
| GET | `/api/schema/` | No | OpenAPI schema (JSON) |
| GET | `/docs/` | No | Interactive Swagger UI documentation |
| GET | `/admin/` | Session (admin) | Django admin panel |

## 🐛 Troubleshooting

### Port Already in Use
- Change port in `docker-compose.yml` or use a different port:
  ```bash
  python manage.py runserver 8001
  ```

### Migration Issues
```bash
python manage.py makemigrations
python manage.py migrate
```

### Postgres Port Conflict
If port `5432` is already used by a locally installed Postgres service,
the `db` container in `docker-compose.yml` is mapped to host port `5433`
instead. Set `POSTGRES_PORT=5433` in `.env` when running Django outside
Docker; inside Docker the `web` service always talks to `db:5432`. When
connecting with a tool like pgAdmin, make sure it targets port `5433`,
not the default `5432` — otherwise it will show an empty, unrelated
Postgres instance.

### "Failed to fetch" in Swagger UI
Usually means the dev server isn't running or crashed — check your
terminal and restart it with `python manage.py runserver`.

## 📝 Development Notes

### How It Works
1. User registers/logs in and receives a JWT access + refresh token pair
2. User submits a long URL via `POST /api/v1/urls/` with `Authorization: Bearer <access-token>`, optionally with a custom alias, metadata, expiry, and tags
3. The service generates a unique short code (or uses the custom alias) and persists the URL in PostgreSQL
4. The short code → original URL mapping is also cached in Redis for fast lookups
5. Visiting `/{short_code}/` looks up an active, non-expired URL, atomically increments `click_count`, records a `Click`, then redirects (302)
6. Premium owners can pull aggregated click analytics (by country, by day, top referrers) for any of their URLs

### Key Design Decisions
- **PostgreSQL as source of truth**: URLs, users, and clicks are persisted in Postgres; Redis is a lookup cache in front of it, not primary storage
- **JWT-only authentication**: No session or token-table auth — access/refresh tokens issued by `djangorestframework-simplejwt`
- **Custom alias reuses `short_code`**: when a caller supplies `custom_alias`, it becomes the actual `short_code` (validated for uniqueness), so redirect lookups always go through a single indexed column
- **Soft delete**: `DELETE /api/v1/urls/{short_code}/` deactivates rather than hard-deletes, preserving click history
- **N+1 prevention**: list/detail views always go through `Url.objects.with_related()` (`select_related('owner')` + `prefetch_related('tags')`)
- **Docker**: Easy deployment and consistent environments

## 🚢 Production Deployment

For production deployment:

1. Update `.env` with production values:
   - Set `DEBUG=False`
   - Use a strong, randomly generated `SECRET_KEY` (JWT signing depends on it)
   - Configure `ALLOWED_HOSTS`
   - Set `CORS_ALLOW_ALL_ORIGINS=False` and list real origins in `CORS_ALLOWED_ORIGINS`

2. Serve via Gunicorn behind a reverse proxy (e.g. nginx), as configured in the `web` service's command in `docker-compose.yml`

3. Ensure the `db` and `redis` volumes are backed up appropriately

## 📄 License

This project is created for educational purposes as part of the Python Backend course.

## 👨‍💻 Author

Created as Module 6: ORM & Data Access Layer — URL Shortener Microservice

---

**Happy URL Shortening! 🎉**
