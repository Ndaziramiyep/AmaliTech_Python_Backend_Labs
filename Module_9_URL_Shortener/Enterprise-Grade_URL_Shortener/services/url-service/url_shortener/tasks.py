import logging

from celery import shared_task
from django.utils import timezone

from url_shortener.caching import invalidate_cache
from url_shortener.clients import analytics_client, preview_client
from url_shortener.clients.analytics_client import AnalyticsServiceUnavailable
from url_shortener.clients.preview_client import PreviewServiceUnavailable
from url_shortener.models import Url

logger = logging.getLogger(__name__)

# Retry policy shared by both analytics-service tasks below: exponential
# backoff (capped, jittered so a bunch of retrying tasks don't all hammer
# analytics-service back to life at the same instant) for up to ~5 attempts
# before giving up and letting Celery log the task as failed.
_ANALYTICS_RETRY_KWARGS = dict(
    autoretry_for=(AnalyticsServiceUnavailable,),
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    max_retries=5,
)

# Same shape, for preview-service.
_PREVIEW_RETRY_KWARGS = dict(
    autoretry_for=(PreviewServiceUnavailable,),
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    max_retries=5,
)


@shared_task(name="url_shortener.tasks.archive_expired_urls")
def archive_expired_urls():
    """Nightly Celery Beat job: archives every URL past its expires_at and evicts it from cache."""
    expired = list(Url.objects.filter(expires_at__isnull=False, expires_at__lte=timezone.now(), is_archived=False))
    for url_obj in expired:
        invalidate_cache(url_obj)

    count = Url.objects.filter(id__in=[url_obj.id for url_obj in expired]).update(
        is_archived=True, is_active=False, archived_at=timezone.now(),
    )
    logger.info("Archived %d expired URL(s)", count)
    return count


@shared_task(name="url_shortener.tasks.record_click", **_ANALYTICS_RETRY_KWARGS)
def record_click_task(short_code, owner_id, referrer="", user_agent="", ip_address=None):
    """Reports a click to analytics-service off the request path — queued via the broker so a redirect never waits on, or loses data to, a downed dependency; retried with backoff if analytics-service is unreachable."""
    analytics_client.record_click(
        short_code=short_code, owner_id=owner_id, referrer=referrer, user_agent=user_agent, ip_address=ip_address,
    )


@shared_task(name="url_shortener.tasks.delete_click_events", **_ANALYTICS_RETRY_KWARGS)
def delete_click_events_task(short_codes):
    """Cascades a URL deletion to analytics-service's click history; retried with backoff if analytics-service is unreachable."""
    analytics_client.delete_click_events(short_codes)


@shared_task(name="url_shortener.tasks.fetch_url_preview", **_PREVIEW_RETRY_KWARGS)
def fetch_url_preview_task(url_id):
    """Fetches title/description/favicon for a newly created Url from preview-service, off the request path so URL creation never waits on — or fails because of — a slow or unreachable destination site.

    Fills in only whichever of those three fields the owner didn't already
    supply explicitly on create — an owner-supplied value always wins.
    Silently does nothing if the Url has since been deleted.
    """
    try:
        url_obj = Url.objects.get(id=url_id)
    except Url.DoesNotExist:
        return

    preview = preview_client.fetch_preview(url_obj.original_url)

    updates = {
        field: preview[field]
        for field in ("title", "description", "favicon")
        if not getattr(url_obj, field) and preview.get(field)
    }
    if updates:
        Url.objects.filter(id=url_id).update(**updates)
