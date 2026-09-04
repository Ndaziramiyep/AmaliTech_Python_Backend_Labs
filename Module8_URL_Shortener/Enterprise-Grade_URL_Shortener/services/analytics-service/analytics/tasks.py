from celery import shared_task

from analytics.models import ClickEvent


@shared_task(name="analytics.tasks.track_click")
def track_click_task(short_code, owner_id, referrer="", user_agent="", ip_address=None, city=None, country=None):
    """Write-behind persistence of a single click event, run off the request path by a Celery worker."""
    ClickEvent.objects.create(
        short_code=short_code,
        owner_id=owner_id,
        referrer=referrer,
        user_agent=user_agent,
        ip_address=ip_address,
        city=city,
        country=country,
    )
