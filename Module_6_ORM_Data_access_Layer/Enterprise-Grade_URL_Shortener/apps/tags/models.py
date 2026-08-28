"""Tag model used to categorize shortened URLs."""

from django.db import models


class Tag(models.Model):
    """Represents a category label that can be attached to many shortened URLs."""

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        """Return the tag's name as its human-readable representation."""
        return self.name
