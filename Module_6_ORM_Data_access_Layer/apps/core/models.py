"""Shared abstract model mixins reused across the project's apps."""

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model that tracks when a record was created and last updated."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
