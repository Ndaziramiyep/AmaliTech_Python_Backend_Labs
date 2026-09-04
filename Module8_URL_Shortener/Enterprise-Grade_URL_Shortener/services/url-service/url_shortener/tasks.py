import logging

from celery import shared_task
from django.utils import timezone

from url_shortener.caching import invalidate_cache
from url_shortener.models import Url

logger = logging.getLogger(__name__)


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
