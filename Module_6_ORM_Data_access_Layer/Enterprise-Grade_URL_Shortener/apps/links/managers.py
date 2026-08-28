"""Custom queryset and manager encapsulating reusable URL query logic."""

from django.db import models
from django.utils import timezone


class URLQuerySet(models.QuerySet):
    """Adds domain-specific filters and query-optimization helpers to the base queryset."""

    def active_urls(self):
        """Return URLs that are active and either never expire or have not expired yet."""
        now = timezone.now()
        return self.filter(is_active=True).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )

    def expired_urls(self):
        """Return URLs whose expiry timestamp has already passed."""
        return self.filter(expires_at__isnull=False, expires_at__lte=timezone.now())

    def popular_urls(self):
        """Return URLs ordered by click count, most popular first."""
        return self.order_by("-click_count")

    def with_related(self):
        """Return URLs with their owner and tags preloaded to avoid N+1 queries."""
        return self.select_related("owner").prefetch_related("tags")


class URLManager(models.Manager):
    """Custom manager that exposes the URLQuerySet's convenience methods at the manager level."""

    def get_queryset(self):
        """Return the custom queryset used for every manager-level lookup."""
        return URLQuerySet(self.model, using=self._db)

    def active_urls(self):
        """Delegate to the queryset's active_urls filter."""
        return self.get_queryset().active_urls()

    def expired_urls(self):
        """Delegate to the queryset's expired_urls filter."""
        return self.get_queryset().expired_urls()

    def popular_urls(self):
        """Delegate to the queryset's popular_urls ordering."""
        return self.get_queryset().popular_urls()

    def with_related(self):
        """Delegate to the queryset's with_related optimization."""
        return self.get_queryset().with_related()
