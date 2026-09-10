"""
Django settings for the url-preview service.
"""

from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-!)diti+gc-$tqv2v!1t1v0t_v45^xa#)fb)ce*6g*o52f$7qgg",
)

DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
if "*" in ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must not contain the '*' wildcard for url-preview.")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.preview",
    "rest_framework",
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

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"


# Database — provisioned for parity with auth/shortener/analytics (the
# shared Dockerfile unconditionally runs `manage.py migrate` on start), but
# this service has no domain tables of its own: the only migration that
# actually runs is Django's own contenttypes. It's genuinely stateless
# beyond Redis (the result cache and the circuit breaker's state).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
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

# REST Framework Configuration — no JWT here: the only endpoint this service
# exposes (PreviewView) is internal-only, gated by IsInternalService instead.
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Shared secret shortener (url-service) sends as X-Internal-Token — the only
# caller allowed to reach this service's one endpoint. Must match
# url-service's own copy of the same value.
INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN", default="")

# Backs both the short-lived result cache and the per-domain circuit
# breaker — both Redis-backed so state is shared across replicas rather than
# living in one process's memory.
REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/0")

# Preview-fetch tuning — see README.md's Environment Variables table.
PREVIEW_FETCH_TIMEOUT = env.float("PREVIEW_FETCH_TIMEOUT", default=5.0)
PREVIEW_MAX_ATTEMPTS = env.int("PREVIEW_MAX_ATTEMPTS", default=3)
PREVIEW_RETRY_BASE_DELAY = env.float("PREVIEW_RETRY_BASE_DELAY", default=0.5)
PREVIEW_MAX_BODY_BYTES = env.int("PREVIEW_MAX_BODY_BYTES", default=2_000_000)
PREVIEW_CIRCUIT_FAILURE_THRESHOLD = env.int("PREVIEW_CIRCUIT_FAILURE_THRESHOLD", default=5)
PREVIEW_CIRCUIT_OPEN_SECONDS = env.int("PREVIEW_CIRCUIT_OPEN_SECONDS", default=60)
PREVIEW_CACHE_TTL = env.int("PREVIEW_CACHE_TTL", default=600)

# drf-spectacular Configuration
SPECTACULAR_SETTINGS = {
    "TITLE": "URL Preview Service API",
    "DESCRIPTION": "Internal-only service that fetches a destination page's title/description/favicon for the URL shortener platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# CORS Configuration — irrelevant in practice (this service is never called
# from a browser, only server-to-server from url-service), kept only for
# parity with the other services' settings.
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=DEBUG)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# Logging Configuration — structured JSON to stdout and to a rotating
# logs/url-preview.log (10MB per file, 5 backups kept); 500s
# (django.request) and security warnings (django.security) are always
# captured. RotatingFileHandler doesn't create missing parent dirs, and
# logs/ is gitignored, so a fresh checkout or image build has to have it
# created here first.
(BASE_DIR / "logs").mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "config.json_logging.JSONFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "url-preview.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
