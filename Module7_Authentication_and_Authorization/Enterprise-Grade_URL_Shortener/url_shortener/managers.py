from django.db import models
from django.utils import timezone


class URLQuerySet(models.QuerySet):
    def active_urls(self):
        now = timezone.now()
        return self.filter(is_active=True).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )

    def expired_urls(self):
        return self.filter(expires_at__isnull=False, expires_at__lte=timezone.now())

    def popular_urls(self):
        return self.order_by('-click_count')

    def with_related(self):
        return self.select_related('owner').prefetch_related('tags')


URLManager = models.Manager.from_queryset(URLQuerySet)
