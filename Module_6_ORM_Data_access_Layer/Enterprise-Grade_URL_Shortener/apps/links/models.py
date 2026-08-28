"""URL model representing a shortened link and its metadata."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.tags.models import Tag

from .managers import URLManager


class URL(TimeStampedModel):
    """Represents a shortened URL, its ownership, tags, and click statistics."""

    original_url = models.URLField(max_length=2000)
    short_code = models.CharField(max_length=10, unique=True)
    custom_alias = models.CharField(max_length=50, unique=True, null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="urls"
    )
    tags = models.ManyToManyField(Tag, related_name="urls", blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    favicon = models.CharField(max_length=255, null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)

    objects = URLManager()

    class Meta:
        # short_code already carries a unique index; created_at gets one explicitly for fast recency queries.
        indexes = [models.Index(fields=["created_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        """Return the short code as this URL's human-readable representation."""
        return self.short_code

    @property
    def is_expired(self) -> bool:
        """Return whether this URL's expiry timestamp has already passed."""
        return bool(self.expires_at and self.expires_at <= timezone.now())
