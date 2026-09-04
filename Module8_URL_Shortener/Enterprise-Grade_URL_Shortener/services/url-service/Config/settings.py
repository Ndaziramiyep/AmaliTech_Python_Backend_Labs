"""
Django settings for the url-service project.
"""

import sys
from datetime import timedelta
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# True when running under `manage.py test` — used to run Celery tasks
# synchronously (no broker needed) instead of enqueueing them for real.
TESTING = "test" in sys.argv


SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-!)diti+gc-$tqv2v!1t1v0t_v45^xa#)fb)ce*6g*o52f$7qgg",
)

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "url_shortener",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "Config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Config.wsgi.application"


# Database
# url-service does NOT own the Users table — django.contrib.auth is only
# installed here for this service's own local Django admin login. Business
# API auth is stateless JWT verification (see url_shortener/security/authentication.py).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "url_shortener.security.authentication.StatelessJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    # Fallback only — TieredUserRateThrottle overrides this per-request based
    # on the caller's tier claim (see url_shortener/api/throttling.py).
    "DEFAULT_THROTTLE_RATES": {
        "tiered_user": "100/day",
    },
}

# JWT Configuration — SIGNING_KEY must match auth-service's JWT_SECRET_KEY so
# tokens it issues verify here. This service only ever reads tokens; it never
# issues them, so REFRESH_TOKEN_LIFETIME is unused but kept for parity.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "SIGNING_KEY": env("JWT_SECRET_KEY", default="change-me-shared-jwt-signing-key"),
}

# Shared secret url-service sends as X-Internal-Key when reporting click
# events to analytics-service, so that endpoint can reject public traffic.
INTERNAL_API_KEY = env("INTERNAL_API_KEY", default="change-me-shared-internal-key")

ANALYTICS_SERVICE_URL = env("ANALYTICS_SERVICE_URL", default="http://localhost:8003")

# drf-spectacular Configuration
SPECTACULAR_SETTINGS = {
    "TITLE": "URL Shortener Service API",
    "DESCRIPTION": "URL shortening and redirect service for the URL shortener platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Cache Configuration - Using Redis for fast URL lookups
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

BASE_URL = env("BASE_URL", default="http://localhost:8002")

# Seconds a short_code -> url data lookup is kept in the cache
URL_CACHE_TIMEOUT_SECONDS = env.int("URL_CACHE_TIMEOUT_SECONDS", default=3600)

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=DEBUG)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# Celery Configuration — a separate Redis DB index from the cache (LOCATION
# above) so task/broker keys never collide with cached URL lookups.
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/2")
CELERY_RESULT_BACKEND = None
CELERY_TASK_IGNORE_RESULT = True
CELERY_TIMEZONE = TIME_ZONE
# Runs tasks inline (no broker/worker needed) under `manage.py test`.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=TESTING)
CELERY_TASK_EAGER_PROPAGATES = True

# Logging Configuration — structured JSON to stdout; 500s (django.request)
# and security warnings (django.security) are always captured.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "url_shortener.logging_utils.JSONFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
