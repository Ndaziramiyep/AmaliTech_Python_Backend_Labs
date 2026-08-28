# URL Shortener Microservice

A URL shortener microservice built with Django REST Framework, featuring JWT authentication, Redis-backed caching, PostgreSQL persistence, Docker containerization, and interactive API documentation with Swagger UI.

## 🚀 Features

- **JWT Authentication**: Register and log in with email + password; every short-URL operation is scoped to the authenticated user
- **URL Shortening**: Convert long URLs into short, shareable links tied to their owner
- **Automatic Redirect**: Short URLs automatically redirect (302) to their original URL
- **Redis Caching**: Fast short-code lookups cached in Redis, backed by PostgreSQL as the source of truth
- **REST API**: Clean RESTful API with proper HTTP status codes
- **API Documentation**: Interactive Swagger UI for testing endpoints
- **Docker Support**: Fully containerized with Docker Compose (Postgres + Redis + web)
- **Admin Panel**: Django admin interface for managing users and URLs

## 🛠️ Technology Stack

- **Framework**: Django 5.0 + Django REST Framework
- **Authentication**: JWT via `djangorestframework-simplejwt`
- **Database**: PostgreSQL (via `psycopg` v3)
- **Cache**: Redis (`django-redis`)
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Server**: Gunicorn (production)
- **Containerization**: Docker & Docker Compose

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

3. **Access the application**
   - API Documentation (Swagger): http://localhost:8000/docs/
   - Django Admin: http://localhost:8000/admin/
   - API Endpoint: http://localhost:8000/api/urls/

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

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser** (optional, for admin access)
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

## 📚 API Usage

All endpoints except registration, login, token refresh, and the redirect endpoint require a JWT access token sent as `Authorization: Bearer <access-token>`.

### 1. Register

**Endpoint**: `POST /api/auth/register/`

**Request Body**:
```json
{
  "email": "alice@example.com",
  "password": "StrongPassword123",
  "confirm_password": "StrongPassword123"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "email": "alice@example.com",
  "access": "<jwt-access-token>",
  "refresh": "<jwt-refresh-token>"
}
```

### 2. Login

**Endpoint**: `POST /api/auth/login/`

**Request Body**:
```json
{
  "email": "alice@example.com",
  "password": "StrongPassword123"
}
```

**Response** (200 OK): same shape as register — `id`, `email`, `access`, `refresh`.

### 3. Refresh Access Token

**Endpoint**: `POST /api/auth/refresh/`

**Request Body**:
```json
{
  "refresh": "<jwt-refresh-token>"
}
```

**Response** (200 OK):
```json
{
  "access": "<new-jwt-access-token>"
}
```

### 4. Create Short URL

**Endpoint**: `POST /api/urls/` (requires `Authorization: Bearer <access-token>`)

**Request Body**:
```json
{
  "original_url": "https://www.example.com"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "original_url": "https://www.example.com",
  "short_url": "abc123",
  "short_link": "http://localhost:8000/abc123/",
  "owner": "alice@example.com",
  "created_at": "2026-01-23T14:00:00Z"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/urls/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access-token>" \
  -d '{"original_url": "https://www.google.com"}'
```

### 5. Look Up the Original URL (no redirect)

**Endpoint**: `GET /api/urls/{short_code}/`

Returns the original URL as JSON instead of redirecting — useful for testing in Swagger, since Swagger's "Try it out" follows real redirects and dumps the destination page's raw HTML.

**Response** (200 OK):
```json
{
  "short_url": "abc123",
  "original_url": "https://www.example.com"
}
```

### 6. Redirect to Original URL

**Endpoint**: `GET /{short_code}/`

**Example**:
- Paste directly into a browser: http://localhost:8000/abc123/
- Redirects to: https://www.example.com

**Response**: 302 Found (redirect)

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Test Coverage
The test suite includes:
- Model tests
- Service layer tests
- Authentication (register/login) tests
- API endpoint tests
- Integration tests

## 📁 Project Structure

```
Enterprise-Grade_URL_Shortener/
├── Config/                       # Django project settings (modular config app)
│   ├── settings.py               # Settings, loaded from environment variables (.env)
│   ├── urls.py                   # Root URL routing + Swagger endpoints
│   ├── wsgi.py                   # WSGI configuration
│   └── asgi.py                   # ASGI configuration
├── url_shortener/                # Main application
│   ├── models.py                 # Url model (owned by a User)
│   ├── admin.py                  # Admin configuration
│   ├── domain/                   # Abstract interfaces (generator, repository, cache)
│   ├── services/                 # Business logic implementing the domain interfaces
│   ├── api/                      # DRF serializers, views (auth + URLs), and URL routing
│   └── tests/                    # Test suite (models, services, auth, API)
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
| POST | `/api/auth/register/` | No | Register with email/password/confirm_password, returns JWT tokens |
| POST | `/api/auth/login/` | No | Log in with email/password, returns JWT tokens |
| POST | `/api/auth/refresh/` | No | Exchange a refresh token for a new access token |
| POST | `/api/urls/` | Yes | Create a new short URL |
| GET | `/api/urls/{short_code}/` | No | Return the original URL as JSON (no redirect) |
| GET | `/{short_code}/` | No | Redirect to the original URL |
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
2. User submits a long URL via `POST /api/urls/` with `Authorization: Bearer <access-token>`
3. The service generates a unique short code and persists the URL (owner, original URL, short code) in PostgreSQL
4. The short code → original URL mapping is also cached in Redis for fast lookups
5. Visiting `/{short_code}/` checks Redis first, falling back to PostgreSQL on a cache miss, then redirects (302)

### Key Design Decisions
- **PostgreSQL as source of truth**: URLs and users are persisted in Postgres; Redis is a lookup cache in front of it, not primary storage
- **JWT-only authentication**: No session or token-table auth — access/refresh tokens issued by `djangorestframework-simplejwt`
- **Unique Short Codes**: Random generation with collision checking against the database
- **RESTful Design**: Proper HTTP methods and status codes
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

Created as Lab 1: URL Shortener Microservice

---

**Happy URL Shortening! 🎉**
