import redis
from django.conf import settings

_client = None


def get_redis_client():
    """Returns a process-wide redis-py client connected to REDIS_URL, created lazily on first use."""
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client
