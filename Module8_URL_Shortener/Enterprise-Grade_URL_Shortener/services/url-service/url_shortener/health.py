import logging

from django.db import connection
from django.http import JsonResponse
from django_redis import get_redis_connection

logger = logging.getLogger(__name__)


def _check_database():
    """True if a query round-trips successfully against the default database."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception:
        logger.error("Health check: database connectivity failed", exc_info=True)
        return False


def _check_redis():
    """True if the Redis server backing the cache responds to a PING."""
    try:
        get_redis_connection("default").ping()
        return True
    except Exception:
        logger.error("Health check: Redis connectivity failed", exc_info=True)
        return False


def health_check(request):
    """Reports overall service health, verifying database and Redis connectivity."""
    checks = {"database": _check_database(), "redis": _check_redis()}
    healthy = all(checks.values())
    return JsonResponse({"status": "ok" if healthy else "unavailable", "checks": checks}, status=200 if healthy else 503)
