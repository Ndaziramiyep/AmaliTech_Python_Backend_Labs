# URL Shortener Microservice

A simple, beginner-friendly URL shortener microservice built with Django REST Framework, featuring built-in caching, Docker containerization, and interactive API documentation with Swagger UI.

## 🚀 Features

- **URL Shortening**: Convert long URLs into short, shareable links
- **Automatic Redirect**: Short URLs automatically redirect to original URLs
- **Built-in Caching**: Fast URL lookups with Django's local memory cache
- **REST API**: Clean RESTful API with proper HTTP status codes
- **API Documentation**: Interactive Swagger UI for testing endpoints
- **Docker Support**: Fully containerized with Docker Compose
- **Admin Panel**: Django admin interface for managing URLs

## 🛠️ Technology Stack

- **Framework**: Django 5.0 + Django REST Framework
- **Cache**: Redis (in-memory data store)
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Server**: Gunicorn (production)
- **Containerization**: Docker & Docker Compose
- **Database**: SQLite (default, easily switchable to PostgreSQL)

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized setup)

## 🔧 Setup Instructions

### Option 1: Run with Docker (Recommended)

1. **Clone the repository**
   ```bash
   cd c:\Users\Amalitech\Desktop\amali\Labs\Labs\module5
   ```

2. **Build and start containers**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - API Documentation (Swagger): http://localhost:8000/api/docs/
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

### 1. Create Short URL

**Endpoint**: `POST /api/urls/`

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
  "created_at": "2026-01-23T14:00:00Z"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/urls/ \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.google.com"}'
```

### 2. Redirect to Original URL

**Endpoint**: `GET /{short_code}/`

**Example**: 
- Visit: http://localhost:8000/abc123/
- Redirects to: https://www.example.com

**Response**: 302 Found (redirect)

## 🧪 Testing

### Run Tests
```bash
python manage.py test url_shortener
```

### Test Coverage
The test suite includes:
- Model tests
- Service layer tests
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
│   ├── models.py                 # Url model
│   ├── admin.py                  # Admin configuration
│   ├── domain/                   # Abstract interfaces (generator, repository, cache)
│   ├── services/                 # Business logic implementing the domain interfaces
│   ├── api/                      # DRF serializers, views, and URL routing
│   └── tests/                    # Test suite (models, services, API)
├── manage.py                     # Django management script
├── Dockerfile                    # Docker image build
├── docker-compose.yml            # db (Postgres) + redis + web services
├── requirements.txt              # Python dependencies
├── .env / .env.example           # Environment configuration
└── README.md                     # This file
```

## 🎯 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/urls/` | Create a new short URL |
| GET | `/{short_code}/` | Redirect to original URL |
| GET | `/api/schema/` | OpenAPI schema (JSON) |
| GET | `/api/docs/` | Interactive Swagger UI documentation |
| GET | `/admin/` | Django admin panel |

## 🐛 Troubleshooting

### Port Already in Use
- Change port in `docker-compose.yml` or use different port:
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
Docker; inside Docker the `web` service always talks to `db:5432`.

## 📝 Development Notes

### How It Works
1. User submits a long URL via POST request
2. Service generates a unique 6-character short code
3. URL mapping is stored in both Redis (primary) and SQLite (backup)
4. Short code is cached in Redis for ultra-fast lookups
5. When user visits short URL, Redis provides instant redirect

### Key Design Decisions
- **Redis Caching**: Uses Redis for 100x faster URL lookups
- **Unique Short Codes**: Random generation with collision checking
- **RESTful Design**: Proper HTTP methods and status codes
- **Docker**: Easy deployment and consistent environments

## 🚢 Production Deployment

For production deployment:

1. Update `.env` with production values:
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure `ALLOWED_HOSTS`

2. Use production Docker target:
   ```bash
   docker-compose -f docker-compose.prod.yml up
   ```

3. Use PostgreSQL instead of SQLite (recommended)

4. Set up proper reverse proxy (nginx)

## 📄 License

This project is created for educational purposes as part of the Python Backend course.

## 👨‍💻 Author

Created as Lab 1: URL Shortener Microservice

---

**Happy URL Shortening! 🎉**
