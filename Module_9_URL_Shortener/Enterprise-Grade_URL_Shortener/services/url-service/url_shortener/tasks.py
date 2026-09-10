import logging

from celery import shared_task
from django.utils import timezone

from url_shortener.caching import invalidate_cache
from url_shortener.clients import preview_client
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


@shared_task(name="url_shortener.tasks.fetch_url_preview")
def fetch_url_preview_task(url_id):
    """Fetches title/description/favicon for a newly created Url from url-preview, off the request path.

    Fills in only whichever of title/description/favicon the owner didn't
    already supply explicitly on create — an owner-supplied value always
    wins. Silently does nothing if the Url has since been deleted, or if
    url-preview couldn't produce a preview at all (preview_client.fetch_preview
    logs and returns None rather than raising, so a slow/unreachable/blocked
    url-preview never fails this task — including under
    CELERY_TASK_ALWAYS_EAGER, where a raised exception would otherwise
    propagate straight back into the view that called .delay()).
    """
    try:
        url_obj = Url.objects.get(id=url_id)
    except Url.DoesNotExist:
        return

    preview = preview_client.fetch_preview(url_obj.original_url)
    if not preview:
        return

    updates = {
        field: preview[field]
        for field in ("title", "description", "favicon")
        if not getattr(url_obj, field) and preview.get(field)
    }
    if updates:
        Url.objects.filter(id=url_id).update(**updates)
