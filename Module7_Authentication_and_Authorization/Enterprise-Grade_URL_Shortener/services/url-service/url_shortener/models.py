from django.db import models


class Tag(models.Model):
    """A named label that can be attached to any number of URLs."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        """Return the tag's name as its string representation."""
        return self.name


class Url(models.Model):
    """A shortened URL mapping, denormalized against auth-service's owner id/email rather than a foreign key."""

    # auth-service owns the canonical User table; this service only ever
    # sees a user's id/email as claims on their JWT, so ownership here is
    # a plain denormalized reference rather than a foreign key.
    owner_id = models.PositiveIntegerField(db_index=True)
    owner_email = models.EmailField()
    original_url = models.URLField(max_length=2000)
    short_url = models.CharField(max_length=10, unique=True)
    # Premium/Admin-only user-chosen alternative to short_url — either one
    # resolves to the same Url (see api/views.py's lookup helpers).
    custom_alias = models.CharField(max_length=50, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    favicon = models.CharField(max_length=2000, null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True, related_name="urls")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the original URL as the model's string representation."""
        return self.original_url
