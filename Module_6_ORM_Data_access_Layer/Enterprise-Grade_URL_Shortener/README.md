# Enterprise-Grade URL Shortener — Module 6

A production-grade URL shortening microservice built with Django 5 and Django REST Framework. This module expands the Module 5 foundation with user ownership, tagging, click analytics, and query-optimized data access.

## Architecture

```
                          ┌────────────────────┐
                          │   config/ (project) │
                          │  settings / urls /  │
                          │   wsgi / asgi        │
                          └──────────┬──────────┘
                                     │
        ┌───────────────┬───────────┼───────────────┬───────────────┐
        ▼               ▼           ▼               ▼               ▼
 ┌─────────────┐ ┌─────────────┐ ┌──────────┐ ┌─────────────┐ ┌─────────────┐
 │ apps/core   │ │apps/accounts│ │apps/tags │ │ apps/links  │ │apps/analytics│
 │             │ │             │ │          │ │             │ │             │
 │ TimeStamped │ │ User model  │ │ Tag model│ │ URL model   │ │ Click model │
 │ abstract    │ │ (email,     │ │ (M2M via │ │ + URLManager│ │ + tracking  │
 │ base model  │ │ tier,       │ │ URL.tags)│ │ + generator │ │   service   │
 │             │ │ is_premium) │ │          │ │ + service   │ │ + aggregate │
 │             │ │             │ │          │ │   layer     │ │   analytics │
 └─────────────┘ └─────────────┘ └──────────┘ └─────────────┘ └─────────────┘
                                        │               │
                                        └───────┬───────┘
                                                 ▼
                                    owner: FK → accounts.User
                                    tags:  M2M → tags.Tag
                                    clicks: reverse FK ← analytics.Click
```

Each app has a single responsibility (SRP): `core` holds shared abstractions, `accounts` owns identity, `tags` owns categorization, `links` owns URL shortening, and `analytics` owns click tracking and reporting. Views depend on service classes rather than embedding business logic, and `URLShortenerService` depends on the `ShortCodeGenerator` abstraction rather than a concrete implementation (DIP), so the generation strategy can be swapped without touching the service or the views.

## Database Schema

| Model | Key fields |
|---|---|
| `accounts.User` | `email` (unique), `is_premium`, `tier` (free/premium/admin) |
| `links.URL` | `original_url`, `short_code` (unique), `custom_alias` (nullable, unique), `owner` (FK), `tags` (M2M), `is_active`, `expires_at`, `click_count` |
| `analytics.Click` | `url` (FK), `clicked_at`, `ip_address`, `city`, `country`, `user_agent`, `referrer` |
| `tags.Tag` | `name` (unique) |

## Module 6 Highlights

- **Custom managers/querysets** (`apps/links/managers.py`): `URL.objects.active_urls()`, `.expired_urls()`, `.popular_urls()`, and `.with_related()`.
- **N+1 prevention**: `with_related()` applies `select_related("owner")` and `prefetch_related("tags")`; the `URLViewSet` queryset always uses it.
- **Indexing**: `short_code` is unique (indexed by the DB), and `created_at` has an explicit index for recency queries.
- **Aggregation**: `URLAnalyticsView` uses `annotate()` with `Count` and `TruncDate` to compute total clicks per country and per day directly in SQL.
- **Data migration**: `apps/tags/migrations/0002_seed_default_tags.py` seeds Marketing, Social, Personal, Business, and Development tags.

## Setup Instructions

### Option 1: Docker (recommended)

```bash
cp .env.example .env
docker-compose up --build
```

- API docs (Swagger): http://localhost:8000/api/docs/
- Django admin: http://localhost:8000/admin/

### Option 2: Local virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Without a `.env` file, the project defaults to SQLite for local development. To use PostgreSQL, copy `.env.example` to `.env` and set `DATABASE_URL`.

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register/` | Create a new account |
| POST | `/api/v1/auth/login/` | Obtain access/refresh JWT |
| POST | `/api/v1/auth/refresh/` | Refresh an access token |

### URL operations (requires authentication)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/urls/` | Create a short URL |
| GET | `/api/v1/urls/` | List the caller's URLs |
| GET | `/api/v1/urls/{short_code}/` | Retrieve a URL's details |
| PUT | `/api/v1/urls/{short_code}/` | Update a URL |
| DELETE | `/api/v1/urls/{short_code}/` | Deactivate a URL |

### Public

| Method | Endpoint | Description |
|---|---|---|
| GET | `/{short_code}/` | Redirect to the original URL (302) and record a click |

### Analytics (premium/admin tier only)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/analytics/{short_code}/` | Click totals by country and by day |

Full interactive documentation is available at `/api/docs/` once the server is running.
