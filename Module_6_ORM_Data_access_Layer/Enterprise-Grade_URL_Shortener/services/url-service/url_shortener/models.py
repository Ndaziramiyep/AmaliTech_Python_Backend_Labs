from django.db import models


class Url(models.Model):
    # auth-service owns the canonical User table; this service only ever
    # sees a user's id/email as claims on their JWT, so ownership here is
    # a plain denormalized reference rather than a foreign key.
    owner_id = models.PositiveIntegerField(db_index=True)
    owner_email = models.EmailField()
    original_url = models.URLField(max_length=2000)
    short_url = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_url
