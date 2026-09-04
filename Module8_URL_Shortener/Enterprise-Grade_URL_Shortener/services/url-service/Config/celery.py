import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Config.settings")

app = Celery("url_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "archive-expired-urls-nightly": {
        "task": "url_shortener.tasks.archive_expired_urls",
        "schedule": crontab(hour=0, minute=0),
    },
}
