import logging

from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def _check_database():
    """True if a query round-trips successfully against the default (SQLite) database."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception:
        logger.error("Health check: database connectivity failed", exc_info=True)
        return False


def health_check(request):
    """Reports overall service health. No Redis/Celery here — this service is stateless, so database is the only dependency."""
    checks = {"database": _check_database()}
    healthy = all(checks.values())
    return JsonResponse({"status": "ok" if healthy else "unavailable", "checks": checks}, status=200 if healthy else 503)
